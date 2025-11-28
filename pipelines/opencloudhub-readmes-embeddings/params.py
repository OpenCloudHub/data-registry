# Data source configuration
DATA_VERSION = "opencloudhub-readmes-download-v1.0.0"
DATA_PATH = "data/opencloudhub-readmes/raw"

# Embedding configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 800
EMBEDDING_CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 4
EMBEDDING_DEVICE = "cpu"

# PostgreSQL/pgvector configuration
PGVECTOR_PORT = 5432
PGVECTOR_DATABASE = "demo_app"
PGVECTOR_USER = "demo-app"
PGVECTOR_TABLE_NAME = "readme_embeddings"

# Analyze output
ANALYZE_OUTPUT_FILE = "../../data/opencloudhub-readmes-embeddings/metadata.json"