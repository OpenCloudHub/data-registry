# ==============================================================================
# Embeddings Pipeline Parameters
# ==============================================================================
#
# Configuration for the README embeddings pipeline. All parameters are read from
# environment variables with sensible defaults for local development.
#
# CONFIGURATION SOURCES:
#   - Production: Kubernetes ConfigMaps (data-job-env, embeddings-env)
#   - Local: .env.docker or .env.minikube files
#   - Fallback: Defaults defined below
#
# DVC tracks this file - changing DEFAULTS triggers pipeline re-run.
# Runtime env var overrides don't trigger re-runs (they're platform config).
#
# ==============================================================================

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================
# ConfigMap: data-job-env (DVC_REPO_URL)
# ConfigMap: embeddings-env (DVC_DATA_VERSION, DVC_DATA_PATH)

DVC_DATA_VERSION = "opencloudhub-readmes-download-v1.0.0"
DVC_DATA_PATH = "data/opencloudhub-readmes-download/raw"
DVC_REPO_URL = "https://github.com/OpenCloudHub/data-registry"

# =============================================================================
# EMBEDDING MODEL CONFIGURATION
# =============================================================================
# ConfigMap: embeddings-env

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 800
EMBEDDING_CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 8

# =============================================================================
# CHUNKING QUALITY FILTERS
# =============================================================================
# ConfigMap: embeddings-env

MIN_CHUNK_SIZE = 50
MAX_NOISE_RATIO = 0.3
