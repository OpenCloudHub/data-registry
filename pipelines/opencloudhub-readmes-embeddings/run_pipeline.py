#!/usr/bin/env python
# ==============================================================================
# DVC Pipeline Runner with Change Detection
# ==============================================================================
#
# Wrapper script for running DVC pipelines in production (Argo Workflows).
# Provides runtime parameter injection and change detection for conditional tagging.
#
# Purpose:
#   In production, we need to:
#   1. Inject runtime parameters (data version) into the pipeline
#   2. Detect if DVC actually produced new outputs (vs cache hit)
#   3. Signal to Argo whether to create new git tags
#
# How It Works:
#   1. Reads DVC_DATA_VERSION and FORCE_RUN from environment variables
#   2. Updates params.py with the runtime data version
#   3. Captures dvc.lock hash BEFORE running pipeline
#   4. Runs `dvc repro` (optionally with --force)
#   5. Compares dvc.lock hash AFTER to detect changes
#   6. Outputs marker: ##DVC_CHANGED=true/false##
#
# The marker is parsed by the Argo workflow to conditionally:
#   - Create git tags only when new data was produced
#   - Skip tagging on cache hits (no wasted versions)
#
# Environment Variables:
#   - DVC_DATA_VERSION: The source data version tag to use
#   - FORCE_RUN: "true" to ignore DVC cache and force re-run
#
# Usage:
#   DVC_DATA_VERSION=opencloudhub-readmes-v1.0.0 python run_pipeline.py
#
# Production:
#   Called by Argo Workflow template 'embeddings-pipeline'
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""
Wrapper script to run DVC pipeline with runtime parameters from env vars.
"""

import hashlib
import os
import re
import subprocess
import sys


def file_hash(path: str) -> str | None:
    """Return MD5 hash of file contents, or None if file doesn't exist."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def main():
    # Read configuration from environment
    data_version = os.environ.get("DVC_DATA_VERSION")
    force = os.environ.get("FORCE_RUN", "false").lower() == "true"

    if not data_version:
        print("ERROR: DVC_DATA_VERSION environment variable not set")
        print("##DVC_CHANGED=error##")
        sys.exit(1)

    print("=" * 60)
    print("DVC Pipeline Runner")
    print("=" * 60)
    print(f"DVC_DATA_VERSION: {data_version}")
    print(f"FORCE_RUN:    {force}")
    print("=" * 60)

    # Update params.py with new DATA_VERSION
    params_file = (
        "/workspace/project/pipelines/opencloudhub-readmes-embeddings/params.py"
    )
    with open(params_file, "r") as f:
        content = f.read()
    content = re.sub(
        r"DVC_DATA_VERSION = .*", f'DVC_DATA_VERSION = "{data_version}"', content
    )
    with open(params_file, "w") as f:
        f.write(content)
    print(f"Updated {params_file}")

    # Hash dvc.lock before running pipeline
    lock_file = "/workspace/project/pipelines/opencloudhub-readmes-embeddings/dvc.lock"
    hash_before = file_hash(lock_file)
    print(f"Lock hash before: {hash_before or 'N/A (new pipeline)'}")

    # Build DVC command
    cmd = ["/workspace/project/.venv/bin/dvc", "repro"]
    if force:
        cmd.append("--force")
    cmd.append("/workspace/project/pipelines/opencloudhub-readmes-embeddings/dvc.yaml")

    print(f"\nRunning: {' '.join(cmd)}\n")

    # Run DVC pipeline
    result = subprocess.run(cmd, cwd="/workspace/project")

    if result.returncode != 0:
        print("\n" + "=" * 60)
        print("ERROR: DVC pipeline failed")
        print("=" * 60)
        print("##DVC_CHANGED=error##")
        sys.exit(result.returncode)

    # Hash dvc.lock after running pipeline
    hash_after = file_hash(lock_file)
    changed = hash_before != hash_after

    # Output summary
    print("\n" + "=" * 60)
    print("Pipeline Complete")
    print("=" * 60)
    print(f"Lock hash before: {hash_before or 'N/A'}")
    print(f"Lock hash after:  {hash_after}")
    print(f"Produced new outputs: {changed}")
    print("=" * 60)

    # Output marker for Argo workflow to parse
    # This MUST be on its own line for reliable grep matching
    print(f"##DVC_CHANGED={str(changed).lower()}##")

    sys.exit(0)


if __name__ == "__main__":
    main()
