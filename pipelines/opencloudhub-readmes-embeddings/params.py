# ==============================================================================
# Embeddings Pipeline Parameters
# ==============================================================================
#
# Configuration for the README embeddings pipeline. These parameters are tracked
# by DVC and used by both analyze.py and process.py scripts.
#
# CONFIGURATION HIERARCHY:
#   1. Environment variables (highest priority) - set by ConfigMaps in production
#   2. params.py defaults (this file) - tracked by DVC, triggers re-runs
#
# WHAT GOES WHERE:
#   - params.py: Pipeline logic defaults (model, chunk size, paths)
#   - Environment: Platform config (URLs, credentials, runtime overrides)
#
# In production (Argo Workflows), ConfigMaps inject env vars to override defaults.
# Locally, use .env.docker or .env.minikube files.
#
# DVC tracks the DEFAULTS below - changing them triggers pipeline re-run.
# Env var overrides don't trigger re-runs (they're runtime config).
#
# ==============================================================================

import os
from pathlib import Path

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================
# These can be overridden by environment variables for production flexibility

# DVC repository URL - where to fetch versioned data from
# Override: DVC_REPO_URL env var (set by data-job-env ConfigMap)
DVC_REPO_URL = os.getenv(
    "DVC_REPO_URL", "https://github.com/OpenCloudHub/data-registry"
)

# Data version tag - which snapshot of data to process
# Override: DVC_DATA_VERSION env var (set per workflow run)
DVC_DATA_VERSION = os.getenv("DVC_DATA_VERSION", "opencloudhub-readmes-v1.0.0")

# Path within DVC repo to source data (rarely changes)
DVC_DATA_PATH = "data/opencloudhub-readmes/raw"

# =============================================================================
# EMBEDDING MODEL CONFIGURATION
# =============================================================================
# These are pipeline logic - tracked by DVC, changing triggers re-run
#
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

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 800
EMBEDDING_CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 8

# =============================================================================
# CHUNKING QUALITY FILTERS
# =============================================================================
# Filter out noise that wastes embedding dimensions

MIN_CHUNK_SIZE = 50  # Skip chunks smaller than this (noise)
MAX_NOISE_RATIO = 0.3  # Skip if >30% ASCII art/box characters

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

ANALYZE_OUTPUT_FILE = (
    Path(__file__).parent.parent.parent
    / "data/opencloudhub-readmes-embeddings/metadata.json"
)
