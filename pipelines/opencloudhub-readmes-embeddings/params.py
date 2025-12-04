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
# ------------------------------------------------------------------------------
# Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
# Alternatives:
#   - all-mpnet-base-v2: Better quality, 768 dims, slower
#   - bge-small-en-v1.5: Optimized for retrieval, 384 dims
#
# Chunk Size: 512-1000 chars is optimal for most retrieval tasks
#   - Too small (<200): Loses context, fragments sentences
#   - Too large (>1500): Dilutes semantic meaning, embedding quality drops
#   - Sweet spot: 500-800 for technical docs
#
# Chunk Overlap: 10-20% of chunk size prevents losing context at boundaries
#   - Helps when relevant info spans chunk boundaries
#   - Too much overlap = redundant storage, slower retrieval
# ------------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 800  # Reduced from 1500 for better semantic density
EMBEDDING_CHUNK_OVERLAP = 100  # ~12% overlap
EMBEDDING_BATCH_SIZE = 8  # Increased for faster processing

# Chunking quality filters
MIN_CHUNK_SIZE = 50  # Skip chunks smaller than this (noise)
MAX_NOISE_RATIO = 0.3  # Skip if >30% ASCII art/box characters

# Output configuration
ANALYZE_OUTPUT_FILE = "../../data/opencloudhub-readmes-embeddings/metadata.json"
