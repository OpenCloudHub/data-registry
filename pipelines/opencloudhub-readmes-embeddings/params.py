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

import os
from pathlib import Path

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================
# ConfigMap: data-job-env (DVC_REPO_URL)
# ConfigMap: embeddings-env (DVC_DATA_VERSION, DVC_DATA_PATH)

DVC_REPO_URL = os.getenv(
    "DVC_REPO_URL", "https://github.com/OpenCloudHub/data-registry"
)
DVC_DATA_VERSION = os.getenv("DVC_DATA_VERSION", "opencloudhub-readmes-v1.0.0")
DVC_DATA_PATH = os.getenv("DVC_DATA_PATH", "data/opencloudhub-readmes/raw")

# =============================================================================
# EMBEDDING MODEL CONFIGURATION
# =============================================================================
# ConfigMap: embeddings-env

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_CHUNK_SIZE = int(os.getenv("EMBEDDING_CHUNK_SIZE", "800"))
EMBEDDING_CHUNK_OVERLAP = int(os.getenv("EMBEDDING_CHUNK_OVERLAP", "100"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "8"))

# =============================================================================
# CHUNKING QUALITY FILTERS
# =============================================================================
# ConfigMap: embeddings-env

MIN_CHUNK_SIZE = int(os.getenv("MIN_CHUNK_SIZE", "50"))
MAX_NOISE_RATIO = float(os.getenv("MAX_NOISE_RATIO", "0.3"))

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================
# ConfigMap: embeddings-env (relative path from pipeline dir)
# Resolved to absolute path for script use

_output_path = os.getenv(
    "ANALYZE_OUTPUT_FILE", "../../data/opencloudhub-readmes-embeddings/metadata.json"
)
# Resolve relative paths from this file's directory
ANALYZE_OUTPUT_FILE = (
    Path(__file__).parent / _output_path
    if not os.path.isabs(_output_path)
    else Path(_output_path)
)
