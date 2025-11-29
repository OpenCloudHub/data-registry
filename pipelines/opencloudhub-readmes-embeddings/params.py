# Data source configuration
DATA_VERSION = "opencloudhub-readmes-v1.0.0"
DATA_PATH = "data/opencloudhub-readmes/raw"

# Embedding model configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 1500
EMBEDDING_CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 4

# Output configuration
PGVECTOR_TABLE_NAME = "readme_embeddings"
ANALYZE_OUTPUT_FILE = "../../data/opencloudhub-readmes-embeddings/metadata.json"
