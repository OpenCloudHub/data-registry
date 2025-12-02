"""
Process README files using Ray Data: chunk, embed, and store to pgvector.
Reads data directly from DVC without intermediate local storage.
"""

import os
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, List

import dvc.api
import psycopg
import ray
import s3fs
import torch
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sentence_transformers import SentenceTransformer

# Add parent directory to path to import params
sys.path.insert(0, str(Path(__file__).parent.parent))
import params


def get_s3_filesystem(endpoint_url: str) -> s3fs.S3FileSystem:
    """Create S3 filesystem for MinIO with SSL verification disabled."""
    return s3fs.S3FileSystem(
        anon=False,
        endpoint_url=endpoint_url,
        key=os.getenv("AWS_ACCESS_KEY_ID"),
        secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
        client_kwargs={"verify": False},
    )


def get_readme_urls(repo: str, data_version: str, data_path: str) -> List[str]:
    """Get URLs for all README files from DVC."""
    print(f"Fetching README URLs from DVC version: {data_version}")

    fs = dvc.api.DVCFileSystem(repo=repo, rev=data_version)
    readme_paths = []

    try:
        for entry in fs.ls(data_path, detail=False):
            if entry.endswith(".md"):
                readme_paths.append(entry)
    except Exception as e:
        raise RuntimeError(f"Failed to list files from DVC: {e}")

    print(f"Found {len(readme_paths)} README files")

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
    """Create the pgvector table compatible with LangChain."""
    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"✓ Dropped existing table '{table_name}' (if any)")

            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            cur.execute(f"""
                CREATE TABLE {table_name} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    embedding VECTOR(384) NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            cur.execute(f"""
                CREATE INDEX {table_name}_embedding_idx
                ON {table_name}
                USING hnsw (embedding vector_cosine_ops)
            """)

            cur.execute(f"""
                CREATE INDEX {table_name}_id_idx
                ON {table_name} (id)
            """)

            conn.commit()

    print(f"✓ Table '{table_name}' initialized with LangChain-compatible schema")


class Chunker:
    """Chunk markdown text by headers first, then by size if needed."""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        # Split by markdown headers first
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
            strip_headers=False,  # Keep headers in the text
        )
        # Then split large sections by size
        self.size_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def _clean_header(self, h: str) -> str:
        # Remove anchor tags like <a id="..."></a>
        return re.sub(r"<a[^>]*></a>", "", h).strip()

    def __call__(self, row: Dict) -> List[Dict]:
        path = Path(row["path"])
        text = row["text"]
        repo_name = path.stem.replace("_README", "")
        doc_id = str(uuid.uuid4())

        chunks = []

        # First split by headers
        header_splits = self.header_splitter.split_text(text)

        chunk_index = 0
        for split in header_splits:
            section_text = split.page_content
            section_headers = split.metadata  # {"h1": "Title", "h2": "Section"}

            # If section is too large, split further by size
            if len(section_text) > self.size_splitter._chunk_size:
                sub_texts = self.size_splitter.split_text(section_text)
            else:
                sub_texts = [section_text]

            for sub_text in sub_texts:
                chunks.append(
                    {
                        "text": sub_text,
                        "source_repo": repo_name,
                        "source_file": path.name,
                        "chunk_index": chunk_index,
                        "doc_id": doc_id,
                        "chunk_id": str(uuid.uuid4()),
                        # Add header context to metadata
                        "section_h1": self._clean_header(section_headers.get("h1", "")),
                        "section_h2": section_headers.get("h2", ""),
                        "section_h3": section_headers.get("h3", ""),
                    }
                )
                chunk_index += 1

        return chunks


class Embedder:
    """Generate embeddings for text chunks using sentence-transformers."""

    def __init__(self, model_name: str, device: str | None = None):
        self.model_name = model_name
        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)
        print(f"Loaded embedding model: {model_name} on {self.model.device}")

    def __call__(self, batch: Dict) -> Dict:
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
            "section_h1": batch.get("section_h1", ""),
            "section_h2": batch.get("section_h2", ""),
            "section_h3": batch.get("section_h3", ""),
        }


class PGVectorWriter:
    """Write embeddings to pgvector database in LangChain-compatible format."""

    def __init__(
        self,
        connection_string: str,
        table_name: str,
        data_version: str,
        embedding_model: str,
        docker_image: str | None = None,
        argo_workflow_uid: str | None = None,
    ):
        self.connection_string = connection_string
        self.table_name = table_name
        self.data_version = data_version
        self.embedding_model = embedding_model
        self.docker_image = docker_image
        self.argo_workflow_uid = argo_workflow_uid
        self._conn = None

    def _get_connection(self):
        """Get a fresh connection, reconnecting if needed."""
        if self._conn is not None:
            try:
                # Test if connection is still alive
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                # Connection is dead, close and reconnect
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

        # Create new connection with timeouts
        self._conn = psycopg.connect(
            self.connection_string,
            connect_timeout=20,
        )
        return self._conn

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_conn", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._conn = None

    def __call__(self, batch: Dict) -> Dict:
        # Fresh connection for each batch - no reuse, no stale connection issues
        with psycopg.connect(self.connection_string, connect_timeout=30) as conn:
            with conn.cursor() as cur:
                for i in range(len(batch["chunk_id"])):
                    record_id = batch["chunk_id"][i]
                    content = batch["text"][i]

                    metadata = {
                        "source_repo": batch["source_repo"][i],
                        "source_file": batch["source_file"][i],
                        "chunk_index": int(batch["chunk_index"][i]),
                        "doc_id": batch["doc_id"][i],
                        "dvc_data_version": self.data_version,
                        "embedding_model": self.embedding_model,
                        "docker_image": self.docker_image,
                        "argo_workflow_uid": self.argo_workflow_uid,
                        "section_h1": batch["section_h1"][i],
                        "section_h2": batch["section_h2"][i],
                        "section_h3": batch["section_h3"][i],
                    }

                    cur.execute(
                        f"""
                        INSERT INTO {self.table_name}
                        (id, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            record_id,
                            content,
                            batch["embeddings"][i].tolist(),
                            psycopg.types.json.Jsonb(metadata),
                        ),
                    )

                conn.commit()

        return {}


def get_connection_string() -> str:
    """Build PostgreSQL connection string from environment variables."""
    host = os.getenv("PGVECTOR_HOST")
    if not host:
        raise ValueError("Environment variable PGVECTOR_HOST not set")

    password = os.getenv("PGVECTOR_PASSWORD")
    if not password:
        raise ValueError("Environment variable PGVECTOR_PASSWORD not set")

    port = os.getenv("PGVECTOR_PORT", "5432")
    database = os.getenv("PGVECTOR_DATABASE")
    if not database:
        raise ValueError("Environment variable PGVECTOR_DATABASE not set")

    user = os.getenv("PGVECTOR_USER")
    if not user:
        raise ValueError("Environment variable PGVECTOR_USER not set")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def main():
    """Main processing pipeline using Ray Data."""
    ray.init()

    data_version = params.DVC_DATA_VERSION
    data_path = params.DVC_DATA_PATH

    repo = os.getenv("DVC_REPO")
    if not repo:
        raise ValueError("Environment variable DVC_REPO not set")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    if not endpoint_url:
        raise ValueError("Environment variable AWS_ENDPOINT_URL not set")

    # Workflow metadata for lineage tracking
    docker_image = os.getenv("DOCKER_IMAGE_TAG")
    argo_workflow_uid = os.getenv("ARGO_WORKFLOW_UID")

    model_name = params.EMBEDDING_MODEL_NAME
    chunk_size = params.EMBEDDING_CHUNK_SIZE
    chunk_overlap = params.EMBEDDING_CHUNK_OVERLAP
    batch_size = params.EMBEDDING_BATCH_SIZE
    device = "cuda" if torch.cuda.is_available() else "cpu"
    table_name = os.getenv("PGVECTOR_TABLE_NAME")

    conn_string = get_connection_string()

    print(f"\n{'=' * 60}")
    print("Initializing database table")
    print(f"{'=' * 60}")
    initialize_table(conn_string, table_name)

    print(f"\n{'=' * 60}")
    print("Fetching README URLs from DVC")
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
    print(f"Docker image: {docker_image}")
    print(f"Workflow UID: {argo_workflow_uid}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 60}\n")

    ds = ray.data.read_text(readme_urls, filesystem=s3_fs, include_paths=True)
    print(f"Loaded {ds.count()} README files")

    ds = ds.flat_map(
        Chunker,
        fn_constructor_kwargs={
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
    )
    print(f"Created {ds.count()} text chunks")

    # Embed and store in pgvector
    ds = ds.map_batches(
        Embedder,
        fn_constructor_kwargs={"model_name": model_name, "device": device},
        batch_size=batch_size,
        num_cpus=4,
    )
    ds = ds.map_batches(
        PGVectorWriter,
        fn_constructor_kwargs={
            "connection_string": conn_string,
            "table_name": table_name,
            "data_version": data_version,
            "embedding_model": model_name,
            "docker_image": docker_image,
            "argo_workflow_uid": argo_workflow_uid,
        },
        batch_size=100,
        num_cpus=1,
    )

    # Trigger execution of all stages
    ds.take_all()

    print(f"\n{'=' * 60}")
    print(f"✓ Processing complete! Embeddings stored in {table_name}")
    print(f"{'=' * 60}\n")

    ray.shutdown()


if __name__ == "__main__":
    main()
