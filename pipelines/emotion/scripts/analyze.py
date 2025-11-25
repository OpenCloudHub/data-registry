"""Compute dataset metadata and statistics for emotion dataset."""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyarrow.parquet as pq
import yaml


def load_split(data_path: Path) -> pd.DataFrame:
    """Load data from Parquet file.

    Args:
        data_path: Path to Parquet file

    Returns:
        DataFrame with text and label columns
    """
    return pq.read_table(data_path).to_pandas()


def compute_text_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute text length statistics.

    Args:
        df: DataFrame with 'text' column

    Returns:
        Dictionary of text statistics
    """
    lengths = df["text"].str.len()
    word_counts = df["text"].str.split().str.len()

    return {
        "char_length_mean": float(lengths.mean()),
        "char_length_std": float(lengths.std()),
        "char_length_min": int(lengths.min()),
        "char_length_max": int(lengths.max()),
        "char_length_median": float(lengths.median()),
        "word_count_mean": float(word_counts.mean()),
        "word_count_std": float(word_counts.std()),
        "word_count_min": int(word_counts.min()),
        "word_count_max": int(word_counts.max()),
        "word_count_median": float(word_counts.median()),
    }


def compute_metadata(data_dir: Path) -> Dict[str, Any]:
    """Compute comprehensive dataset metadata.

    Args:
        data_dir: Directory containing processed data splits

    Returns:
        Dictionary containing all metadata
    """
    # Load data
    train_df = load_split(data_dir / "train" / "train.parquet")
    val_df = load_split(data_dir / "val" / "val.parquet")

    # Get unique labels
    all_labels = sorted(pd.concat([train_df["label"], val_df["label"]]).unique())

    # Build metadata
    metadata = {
        "dataset": {
            "name": "emotions",
            "description": "Emotion classification dataset with text and emotion labels",
            "source": "boltuix/emotions-dataset (HuggingFace)",
        },
        "schema": {
            "features": {
                "text": {
                    "dtype": "string",
                    "description": "Text",
                },
                "label": {
                    "dtype": "string",
                    "description": "Emotion label",
                    "classes": all_labels,
                },
            }
        },
        "splits": {
            "train": {
                "num_samples": len(train_df),
                "num_features": 2,
                "label_distribution": train_df["label"].value_counts().to_dict(),
            },
            "val": {
                "num_samples": len(val_df),
                "num_features": 2,
                "label_distribution": val_df["label"].value_counts().to_dict(),
            },
        },
        "metrics": {
            "train": compute_text_stats(train_df),
            "val": compute_text_stats(val_df),
        },
    }

    return metadata


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["analyze"]
    data_dir = Path(params["data_dir"])
    output_file = Path(params["output_file"])

    print("📊 Computing dataset metadata...")
    metadata = compute_metadata(data_dir)

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Saved metadata to {output_file}")
    print(f"   Train: {metadata['splits']['train']['num_samples']} samples")
    print(f"   Val: {metadata['splits']['val']['num_samples']} samples")
    print(f"   Classes: {len(metadata['schema']['features']['label']['classes'])}")
    print(
        f"   Train stats: mean_chars={metadata['metrics']['train']['char_length_mean']:.1f}, "
        f"mean_words={metadata['metrics']['train']['word_count_mean']:.1f}"
    )
