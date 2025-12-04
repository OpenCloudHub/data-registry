# ==============================================================================
# Embeddings Pipeline Parameters
# ==============================================================================
#
# Configuration for the README embeddings pipeline. These parameters are tracked
# by DVC and used by both analyze.py and process.py scripts.
#
# Parameter Categories:
#   - Data Source: DVC version tag and path to source data
#   - Embedding Model: Model name, chunk size, overlap, batch size
#   - Output: Path to metadata output file
#
# Note: Database connection parameters (PGVECTOR_*) are loaded from environment
# variables to keep secrets out of version control. See .env.docker or .env.minikube.
#
# DVC tracks these parameters in dvc.yaml and will re-run the pipeline if they change.
#
# ==============================================================================

# Data source configuration
DVC_DATA_VERSION = "opencloudhub-readmes-v1.0.0"
DVC_DATA_PATH = "data/opencloudhub-readmes/raw"

# Embedding model configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 1500
EMBEDDING_CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 4

# Output configuration
ANALYZE_OUTPUT_FILE = "../../data/opencloudhub-readmes-embeddings/metadata.json"
