# ==============================================================================
# Emotion Dataset Downloader
# ==============================================================================
#
# Downloads the Emotion classification dataset from HuggingFace.
# Used for text classification demonstrations (NLP pipeline).
#
# Dataset: boltuix/emotions-dataset
#   - Text samples labeled with emotion categories
#   - Categories: joy, sadness, anger, fear, love, surprise
#
# Output:
#   raw/emotions.parquet - Raw dataset in Parquet format
#
# Usage:
#   python scripts/download.py
#
# Configuration:
#   See params.yaml for dataset_name and output_dir settings.
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Download emotion dataset from HuggingFace."""

from pathlib import Path

import yaml
from datasets import load_dataset


def download_emotions(dataset_name: str, output_dir: Path) -> None:
    """Download emotion dataset from HuggingFace.

    Args:
        dataset_name: HuggingFace dataset identifier
        output_dir: Directory to save downloaded files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 Downloading {dataset_name} from HuggingFace...")
    dataset = load_dataset(dataset_name, split="train")

    # Save as parquet
    output_file = output_dir / "emotions.parquet"
    dataset.to_parquet(output_file)

    print(f"✅ Downloaded {len(dataset)} samples to {output_file}")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["download"]
    download_emotions(
        dataset_name=params["dataset_name"],
        output_dir=Path(params["output_dir"]),
    )
