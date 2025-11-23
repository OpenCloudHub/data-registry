"""
Analyze processed README embeddings and generate metadata.
"""

import json
from pathlib import Path

import yaml


def load_params() -> dict:
    """Load parameters from params.yaml"""
    params_path = Path(__file__).parent.parent / "params.yaml"
    return yaml.safe_load(open(params_path))


def analyze_readmes(input_dir: Path) -> dict:
    """
    Analyze README files and generate statistics.

    Args:
        input_dir: Directory containing README markdown files

    Returns:
        Dictionary with analysis metadata
    """
    readme_files = list(input_dir.glob("*.md"))

    # Count total files and repos
    total_files = len(readme_files)
    repo_names = [f.stem.replace("_README", "") for f in readme_files]

    # Calculate file sizes
    file_sizes = [f.stat().st_size for f in readme_files]
    total_size = sum(file_sizes)
    avg_size = total_size / total_files if total_files > 0 else 0

    # Count total characters and lines
    total_chars = 0
    total_lines = 0

    for file in readme_files:
        content = file.read_text(encoding="utf-8")
        total_chars += len(content)
        total_lines += len(content.splitlines())

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
    params = load_params()

    # Get data version from params
    data_version = params["data"]["version"]

    # Input directory
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent.parent.parent / "data" / "readme-embeddings" / "raw"
    output_file = (
        script_dir.parent.parent.parent / "data" / "readme-embeddings" / "metadata.json"
    )

    print(f"\n{'=' * 60}")
    print("Analyzing READMEs")
    print(f"{'=' * 60}")
    print(f"Input directory: {input_dir}")
    print(f"Data version: {data_version}")
    print(f"{'=' * 60}\n")

    # Analyze data
    stats = analyze_readmes(input_dir)

    # Build metadata
    metadata = {
        "data_version": data_version,
        "embedding_model": params["embedding"]["model_name"],
        "chunk_size": params["embedding"]["chunk_size"],
        "chunk_overlap": params["embedding"]["chunk_overlap"],
        "statistics": stats,
    }

    # Save metadata
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
