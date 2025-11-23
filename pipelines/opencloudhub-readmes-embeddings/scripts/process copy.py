"""
Process README files using Ray Data: chunk, embed, and store to pgvector.
Reads data directly from DVC without intermediate local storage.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, List

import dvc.api
import psycopg
import ray
import s3fs
import torch
import yaml
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


def load_params() -> dict:
    """Load parameters from params.yaml"""
    params_path = Path(__file__).parent.parent / "params.yaml"
    return yaml.safe_load(open(params_path))


def get_s3_filesystem(endpoint_url: str) -> s3fs.S3FileSystem:
    """
    Create S3 filesystem for MinIO with SSL verification disabled.

    Args:
        endpoint_url: MinIO endpoint URL

    Returns:
        Configured S3FileSystem instance
    """
    return s3fs.S3FileSystem(
        anon=False,
        endpoint_url=endpoint_url,
        key=os.getenv("AWS_ACCESS_KEY_ID"),
        secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
        client_kwargs={
            "verify": False,  # Disable SSL verification for self-signed certs
        },
    )


def get_readme_urls(repo: str, data_version: str, data_path: str) -> List[str]:
    """
    Get URLs for all README files from DVC.

    Args:
        repo: DVC repository URL
        data_version: Git revision (tag, branch, commit)
        data_path: Path to data directory in the repo

    Returns:
        List of S3 URLs to README files
    """
    print(f"Fetching README URLs from DVC version: {data_version}")

    # List files in the directory
    fs = dvc.api.DVCFileSystem(repo=repo, rev=data_version)
    readme_paths = []

    try:
        for entry in fs.ls(data_path, detail=False):
            if entry.endswith(".md"):
                readme_paths.append(entry)
    except Exception as e:
        raise RuntimeError(f"Failed to list files from DVC: {e}")

    print(f"Found {len(readme_paths)} README files")

    # Get URLs for each file
    urls = []
    for path in readme_paths:
        try:
            url = dvc.api.get_url(path, repo=repo, rev=data_version)
            urls.append(url)
            print(f"  ✓ {Path(path).name} -> {url}")
        except Exception as e:
            print(f"  ✗ Failed to get URL for {path}: {e}")

    return urls


def initialize_table(connection_string: str, table_name: str):
    """
    Create the pgvector table if it doesn't exist.

    Args:
        connection_string: PostgreSQL connection string
        table_name: Name of the table to create
    """
    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cur:
            # Ensure vector extension is enabled
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create table with proper schema
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    chunk_text TEXT NOT NULL,
                    embedding VECTOR(384) NOT NULL,
                    source_repo TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    chunk_index INT NOT NULL,
                    doc_id UUID NOT NULL,
                    chunk_id UUID NOT NULL,
                    data_version TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create HNSW index for fast similarity search
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx 
                ON {table_name} 
                USING hnsw (embedding vector_cosine_ops)
            """)

            conn.commit()

    print(f"✓ Table '{table_name}' initialized successfully")


class Chunker:
    """Chunk markdown text into smaller pieces with metadata."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def __call__(self, row: Dict) -> List[Dict]:
        """
        Process a single markdown file into chunks.

        Args:
            row: Dict with 'path' and 'text' keys

        Returns:
            List of chunk dicts with metadata
        """
        path = Path(row["path"])
        text = row["text"]

        # Extract repo name from filename (e.g., "repo_README.md" -> "repo")
        repo_name = path.stem.replace("_README", "")
        doc_id = str(uuid.uuid4())

        chunks = []
        texts = self.splitter.split_text(text)

        for chunk_index, chunk_text in enumerate(texts):
            chunks.append(
                {
                    "text": chunk_text,
                    "source_repo": repo_name,
                    "source_file": path.name,
                    "chunk_index": chunk_index,
                    "doc_id": doc_id,
                    "chunk_id": str(uuid.uuid4()),
                }
            )

        return chunks


class Embedder:
    """Generate embeddings for text chunks using sentence-transformers."""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.model = SentenceTransformer(
            model_name,
            device=device if torch.cuda.is_available() and device == "cuda" else "cpu",
        )
        print(f"Loaded embedding model: {model_name} on {self.model.device}")

    def __call__(self, batch: Dict) -> Dict:
        """
        Generate embeddings for a batch of text chunks.

        Args:
            batch: Dict with 'text' key containing list of strings

        Returns:
            Dict with embeddings and all original fields
        """
        embeddings = self.model.encode(
            batch["text"], convert_to_numpy=True, show_progress_bar=False
        )

        return {
            "embeddings": embeddings,
            "text": batch["text"],
            "source_repo": batch["source_repo"],
            "source_file": batch["source_file"],
            "chunk_index": batch["chunk_index"],
            "doc_id": batch["doc_id"],
            "chunk_id": batch["chunk_id"],
        }


class PGVectorWriter:
    """Write embeddings to pgvector database."""

    def __init__(
        self,
        connection_string: str,
        table_name: str,
        data_version: str,
        embedding_model: str,
    ):
        self.connection_string = connection_string
        self.table_name = table_name
        self.data_version = data_version
        self.embedding_model = embedding_model
        self._conn = None

    def _init_connection(self):
        """Initialize database connection."""
        if self._conn is None:
            self._conn = psycopg.connect(self.connection_string)

    def __getstate__(self):
        """Exclude connection from pickle state."""
        state = self.__dict__.copy()
        state.pop("_conn", None)
        return state

    def __setstate__(self, state):
        """Restore state and reinitialize connection."""
        self.__dict__.update(state)
        self._conn = None

    def __call__(self, batch: Dict) -> Dict:
        """
        Write a batch of embeddings to pgvector.

        Args:
            batch: Dict with embeddings and metadata

        Returns:
            Empty dict (data is written to database)
        """
        self._init_connection()

        with self._conn.cursor() as cur:
            # Prepare data for batch insert
            for i in range(len(batch["chunk_id"])):
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} 
                    (chunk_text, embedding, source_repo, source_file, 
                     chunk_index, doc_id, chunk_id, data_version, embedding_model)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        batch["text"][i],
                        batch["embeddings"][i].tolist(),
                        batch["source_repo"][i],
                        batch["source_file"][i],
                        int(batch["chunk_index"][i]),
                        batch["doc_id"][i],
                        batch["chunk_id"][i],
                        self.data_version,
                        self.embedding_model,
                    ),
                )

            self._conn.commit()

        return {}


def get_connection_string(params: dict) -> str:
    """Build PostgreSQL connection string from params."""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    pg_config = params["pgvector"]
    password = os.getenv("POSTGRES_DEMO_APP_DB_PASSWORD")

    if not password:
        raise ValueError(
            "Environment variable POSTGRES_DEMO_APP_DB_PASSWORD not set. "
            f"Checked .env file at: {env_path}"
        )

    return (
        f"postgresql://{pg_config['user']}:{password}"
        f"@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
    )


def main():
    """Main processing pipeline using Ray Data."""
    params = load_params()

    # Get data version and path from params
    repo = params["data"]["dvc_repo"]
    data_version = params["data"]["version"]
    data_path = params["data"]["path"]
    endpoint_url = params["data"]["endpoint_url"]

    # Load embedding params
    emb_params = params["embedding"]
    model_name = emb_params["model_name"]
    chunk_size = emb_params["chunk_size"]
    chunk_overlap = emb_params["chunk_overlap"]
    batch_size = emb_params["batch_size"]
    device = emb_params["device"]

    # Get database connection
    conn_string = get_connection_string(params)
    table_name = params["pgvector"]["table_name"]

    # Initialize table (create if not exists)
    print(f"\n{'=' * 60}")
    print("Initializing database table")
    print(f"{'=' * 60}")
    initialize_table(conn_string, table_name)

    # Get URLs for README files from DVC (async but wrapped in sync call)
    print(f"\n{'=' * 60}")
    print("Fetching README URLs from DVC (async)")
    print(f"{'=' * 60}")
    readme_urls = get_readme_urls(repo, data_version, data_path)

    if not readme_urls:
        raise RuntimeError("No README files found in DVC")

    print(f"\n{'=' * 60}")
    print("Creating S3 filesystem for MinIO")
    print(f"{'=' * 60}")
    s3_fs = get_s3_filesystem(endpoint_url)
    print(f"✓ S3 filesystem created for {endpoint_url}")

    print(f"\n{'=' * 60}")
    print("Processing READMEs with Ray Data")
    print(f"{'=' * 60}")
    print(f"Number of files: {len(readme_urls)}")
    print(f"Embedding model: {model_name}")
    print(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
    print(f"Data version: {data_version}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 60}\n")

    # Build Ray Data pipeline - read directly from S3 URLs
    ds = ray.data.read_text(readme_urls, filesystem=s3_fs, include_paths=True)

    print(f"Loaded {ds.count()} README files")

    # Chunk documents
    ds = ds.flat_map(
        Chunker,
        fn_constructor_kwargs={
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
    )

    print(f"Created {ds.count()} text chunks")

    # Generate embeddings
    # Here we coul utilize the power of ray resource management and distrubuted workloads
    ds = ds.map_batches(
        Embedder,
        fn_constructor_kwargs={"model_name": model_name, "device": device},
        batch_size=batch_size,
        num_cpus=4,
    )

    # Write to pgvector
    ds = ds.map_batches(
        PGVectorWriter,
        fn_constructor_kwargs={
            "connection_string": conn_string,
            "table_name": table_name,
            "data_version": data_version,
            "embedding_model": model_name,
        },
        batch_size=100,
        num_cpus=1,
    )

    # Execute pipeline
    ds.take_all()

    print(f"\n{'=' * 60}")
    print(f"✓ Processing complete! Embeddings stored in {table_name}")
    print(f"{'=' * 60}\n")

    ray.shutdown()


if __name__ == "__main__":
    main()
