# ==============================================================================
# Wine Quality Dataset Downloader
# ==============================================================================
#
# Downloads the Wine Quality dataset from UCI ML Repository.
# Used for tabular regression demonstrations.
#
# Dataset: UCI Wine Quality
#   - Physicochemical properties of red and white wines
#   - Target: Quality score (0-10 scale)
#   - Features: acidity, sugar, pH, alcohol, etc.
#
# Output Files:
#   - winequality-red.csv
#   - winequality-white.csv
#
# Citation:
#   P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
#   "Modeling wine preferences by data mining from physicochemical properties."
#   Decision Support Systems, Elsevier, 47(4):547-553, 2009.
#
# Usage:
#   python scripts/download.py
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Download Wine Quality dataset."""

import urllib.request
from pathlib import Path

import yaml


def download_wine_quality(base_url: str, output_dir: Path) -> None:
    """Download Wine Quality dataset files.

    Args:
        base_url: Base URL for the dataset
        output_dir: Directory to save downloaded files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Wine Quality dataset files from UCI ML Repository
    files = {
        "winequality-red.csv": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
        "winequality-white.csv": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
    }

    print("📥 Downloading Wine Quality dataset...")
    for filename, url in files.items():
        filepath = output_dir / filename
        print(f"  Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["download"]
    download_wine_quality(
        base_url=params["base_url"],
        output_dir=Path(params["output_dir"]),
    )
