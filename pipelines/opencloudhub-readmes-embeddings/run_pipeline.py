#!/usr/bin/env python
"""
Wrapper script to run DVC pipeline with runtime parameters from env vars.

This script:
1. Reads DVC_DATA_VERSION and FORCE_RUN from environment variables
2. Updates params.py with the new DVC_DATA_VERSION
3. Runs dvc repro
4. Detects if DVC produced new outputs by comparing dvc.lock hash
5. Outputs a marker (##DVC_CHANGED=true/false##) for Argo to parse

The marker is used by the Argo workflow to conditionally create git tags
only when the pipeline actually produced new outputs (not a cache hit).
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
