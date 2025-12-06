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
#   1. Inject runtime parameters (data version) into params.py as literals
#   2. Let DVC detect changes by comparing params.py against dvc.lock
#   3. Signal to Argo whether to create new git tags
#
# How It Works:
#   1. Reads runtime config from environment variables
#   2. Updates params.py literals (DVC reads these)
#   3. Captures dvc.lock hash BEFORE running pipeline
#   4. Runs `dvc repro` (optionally with --force)
#   5. Compares dvc.lock hash AFTER to detect changes
#   6. Outputs marker: ##DVC_CHANGED=true/false##
#
# Environment Variables:
#   - DVC_DATA_VERSION: The source data version tag to use
#   - DVC_DATA_PATH: Path to data within the DVC repo
#   - EMBEDDING_MODEL_NAME: Model for embeddings
#   - EMBEDDING_CHUNK_SIZE: Chunk size for text splitting
#   - EMBEDDING_CHUNK_OVERLAP: Overlap between chunks
#   - EMBEDDING_BATCH_SIZE: Batch size for embedding
#   - MIN_CHUNK_SIZE: Minimum chunk size filter
#   - MAX_NOISE_RATIO: Maximum noise ratio filter
#   - FORCE_RUN: "true" to ignore DVC cache and force re-run
#
# Usage:
#   DVC_DATA_VERSION=opencloudhub-readmes-v1.0.0 python run_pipeline.py
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

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


def update_params_file(params_file: str, updates: dict[str, any]):
    """Update simple literals in params.py for DVC to detect.

    DVC only parses simple literals (ast.literal_eval compatible).
    This function updates those values before DVC runs.
    """
    with open(params_file, "r") as f:
        content = f.read()

    for key, value in updates.items():
        if value is None:
            continue

        # Format value as Python literal
        if isinstance(value, str):
            literal = f'"{value}"'
        elif isinstance(value, bool):
            literal = "True" if value else "False"
        elif isinstance(value, float):
            literal = str(value)
        elif isinstance(value, int):
            literal = str(value)
        else:
            literal = repr(value)

        # Replace the assignment (handles any whitespace around =)
        pattern = rf"^({key}\s*=\s*).*$"
        replacement = rf"\g<1>{literal}"
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(params_file, "w") as f:
        f.write(content)


def get_env_updates() -> dict[str, any]:
    """Collect parameter updates from environment variables.

    Only includes values that are explicitly set in the environment.
    Missing env vars are skipped (keeps params.py defaults).
    """
    updates = {}

    # String params
    str_params = [
        "DVC_DATA_VERSION",
        "DVC_DATA_PATH",
        "DVC_REPO_URL",
        "EMBEDDING_MODEL_NAME",
    ]
    for param in str_params:
        value = os.environ.get(param)
        if value:
            updates[param] = value

    # Int params
    int_params = [
        "EMBEDDING_CHUNK_SIZE",
        "EMBEDDING_CHUNK_OVERLAP",
        "EMBEDDING_BATCH_SIZE",
        "MIN_CHUNK_SIZE",
    ]
    for param in int_params:
        value = os.environ.get(param)
        if value:
            updates[param] = int(value)

    # Float params
    float_params = ["MAX_NOISE_RATIO"]
    for param in float_params:
        value = os.environ.get(param)
        if value:
            updates[param] = float(value)

    return updates


def main():
    # Paths
    pipeline_dir = "/workspace/project/pipelines/opencloudhub-readmes-embeddings"
    params_file = f"{pipeline_dir}/params.py"
    lock_file = f"{pipeline_dir}/dvc.lock"
    dvc_yaml = f"{pipeline_dir}/dvc.yaml"
    dvc_bin = "/workspace/project/.venv/bin/dvc"

    # Read configuration from environment
    force = os.environ.get("FORCE_RUN", "false").lower() == "true"
    updates = get_env_updates()

    print("=" * 60)
    print("DVC Pipeline Runner")
    print("=" * 60)
    print(f"FORCE_RUN: {force}")
    print("Parameter updates from env:")
    for key, value in updates.items():
        print(f"  {key}: {value}")
    print("=" * 60)

    # Update params.py with runtime values
    if updates:
        update_params_file(params_file, updates)
        print(f"\n✓ Updated {params_file}")
        print("  DVC will compare these against dvc.lock\n")
    else:
        print("\n⚠ No env overrides - using params.py defaults\n")

    # Hash dvc.lock before running pipeline
    hash_before = file_hash(lock_file)
    print(f"Lock hash before: {hash_before or 'N/A (new pipeline)'}")

    # Build DVC command
    cmd = [dvc_bin, "repro"]
    if force:
        cmd.append("--force")
    cmd.append(dvc_yaml)

    print(f"\nRunning: {' '.join(cmd)}\n")
    print("-" * 60)

    # Run DVC pipeline
    result = subprocess.run(cmd, cwd="/workspace/project")

    print("-" * 60)

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
    print(f"##DVC_CHANGED={str(changed).lower()}##")

    sys.exit(0)


if __name__ == "__main__":
    main()
