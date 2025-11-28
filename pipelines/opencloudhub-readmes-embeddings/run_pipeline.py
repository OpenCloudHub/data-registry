#!/usr/bin/env python
"""Wrapper script to run DVC pipeline with runtime parameters from env vars."""

import os
import re
import subprocess
import sys


def main():
    data_version = os.environ.get("DATA_VERSION")
    force = os.environ.get("FORCE_RUN", "false").lower() == "true"

    if not data_version:
        print("ERROR: DATA_VERSION environment variable not set")
        sys.exit(1)

    print(f"DATA_VERSION: {data_version}")
    print(f"FORCE_RUN: {force}")

    # Update params.py with Python (no sed, no shell escaping)
    params_file = (
        "/workspace/project/pipelines/opencloudhub-readmes-embeddings/params.py"
    )
    with open(params_file, "r") as f:
        content = f.read()

    content = re.sub(r"DATA_VERSION = .*", f'DATA_VERSION = "{data_version}"', content)

    with open(params_file, "w") as f:
        f.write(content)

    print(f"Updated {params_file}")

    # Run DVC
    cmd = ["/workspace/project/.venv/bin/dvc", "repro"]
    if force:
        cmd.append("--force")
    cmd.append("/workspace/project/pipelines/opencloudhub-readmes-embeddings/dvc.yaml")

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd="/workspace/project")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
