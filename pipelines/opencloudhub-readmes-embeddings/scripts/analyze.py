# ==============================================================================
# README Embeddings Analyzer
# ==============================================================================
#
# Generates metadata and statistics for the README embeddings pipeline.
# Fetches data directly from DVC at a specific version tag for reproducibility.
#
# Key Features:
#   - Fetches README files from DVC using version tags (e.g., opencloudhub-readmes-v1.0.0)
#   - Computes statistics: file counts, sizes, character/line averages
#   - Records embedding configuration (model, chunk size, overlap)
#   - Outputs metadata.json for tracking in DVC metrics
#
# Environment Variables Required:
#   - DVC_REPO_URL: GitHub repository URL (e.g., https://github.com/OpenCloudHub/data-registry)
#   - AWS_ENDPOINT_URL: MinIO/S3 endpoint for DVC remote access
#   - AWS_ACCESS_KEY_ID: S3 access credentials
#   - AWS_SECRET_ACCESS_KEY: S3 secret credentials
#
# Usage:
#   python scripts/analyze.py
#
# Output:
#   data/opencloudhub-readmes-embeddings/metadata.json
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Analyze processed README embeddings and generate metadata."""

import json
import os
import sys
from pathlib import Path

import dvc.api

# Add parent directory to path to import params
sys.path.insert(0, str(Path(__file__).parent.parent))
import params


def fetch_readme_list(repo: str, data_version: str, data_path: str) -> list:
    """Get list of README files from DVC version."""
    print(f"Fetching README files from DVC repo at version: {data_version}")

    # Configure DVC remote with credentials from environment variables
    remote_config = {
        "endpointurl": os.getenv("AWS_ENDPOINT_URL"),
        "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    }
    # Remove None values
    remote_config = {k: v for k, v in remote_config.items() if v}

    fs = dvc.api.DVCFileSystem(repo=repo, rev=data_version, remote_config=remote_config)

    readmes = []
    for entry in fs.ls(data_path, detail=False):
        if entry.endswith(".md"):
            try:
                # Use fs.open() instead of dvc.api.read() to use credentials
                with fs.open(entry, mode="r", encoding="utf-8") as f:
                    content = f.read()
                filename = Path(entry).name
                readmes.append((filename, content))
            except Exception as e:
                print(f"Warning: Could not read {entry}: {e}")

    return readmes


def analyze_readmes(readmes: list) -> dict:
    """Analyze README files and generate statistics."""
    total_files = len(readmes)
    repo_names = [Path(fname).stem.replace("_README", "") for fname, _ in readmes]

    file_sizes = [len(content.encode("utf-8")) for _, content in readmes]
    total_size = sum(file_sizes)
    avg_size = total_size / total_files if total_files > 0 else 0

    total_chars = sum(len(content) for _, content in readmes)
    total_lines = sum(len(content.splitlines()) for _, content in readmes)

    avg_chars = total_chars / total_files if total_files > 0 else 0
    avg_lines = total_lines / total_files if total_files > 0 else 0

    return {
        "total_files": total_files,
        "total_repositories": len(set(repo_names)),
        "repository_names": sorted(set(repo_names)),
        "total_size_bytes": total_size,
        "average_size_bytes": round(avg_size, 2),
        "total_characters": total_chars,
        "average_characters": round(avg_chars, 2),
        "total_lines": total_lines,
        "average_lines": round(avg_lines, 2),
    }


def main():
    """Generate metadata for README embeddings."""
    data_version = params.DVC_DATA_VERSION
    data_path = params.DVC_DATA_PATH
    output_file = params.ANALYZE_OUTPUT_FILE
    repo = params.DVC_REPO_URL

    print(f"\n{'=' * 60}")
    print("Analyzing READMEs from DVC version")
    print(f"{'=' * 60}")
    print(f"Data version: {data_version}")
    print(f"Data path: {data_path}")
    print(f"{'=' * 60}\n")

    readmes = fetch_readme_list(repo, data_version, data_path)
    stats = analyze_readmes(readmes)

    metadata = {
        "source_data_version": data_version,
        "embedding_model": params.EMBEDDING_MODEL_NAME,
        "chunk_size": params.EMBEDDING_CHUNK_SIZE,
        "chunk_overlap": params.EMBEDDING_CHUNK_OVERLAP,
        "statistics": stats,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Analysis Results:")
    print(f"  Data version: {data_version}")
    print(f"  Total repositories: {stats['total_repositories']}")
    print(f"  Total README files: {stats['total_files']}")
    print(f"  Total size: {stats['total_size_bytes']:,} bytes")
    print(f"  Average file size: {stats['average_size_bytes']:.0f} bytes")
    print(f"  Average lines: {stats['average_lines']:.0f}")
    print(f"\n✓ Metadata saved to: {output_file}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
