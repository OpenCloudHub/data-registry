# ==============================================================================
# Emotion Dataset Processor
# ==============================================================================
#
# Processes raw emotion data: normalizes schema, samples, and splits into
# train/validation sets for ML training.
#
# Processing Steps:
#   1. Normalize column names (Sentence→text, Label→label)
#   2. Sample a fraction of data (configurable, reproducible with seed)
#   3. Split into train/val sets
#   4. Save as Parquet files
#
# Output Schema:
#   - text: string - Sentence text
#   - label: string - Emotion label
#
# Output Structure:
#   processed/
#   ├── train/train.parquet
#   └── val/val.parquet
#
# Usage:
#   python scripts/process.py
#
# Configuration:
#   See params.yaml for sample_fraction, train_split, and random_seed.
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Process emotion dataset: sample and split."""

from pathlib import Path
from typing import Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


def sample_data(df: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    """Sample a fraction of the dataset with reproducible randomness.

    Args:
        df: Input dataframe
        fraction: Fraction of data to keep (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        Sampled dataframe
    """
    if fraction >= 1.0:
        return df
    return df.sample(frac=fraction, random_state=seed)


def split_data(
    df: pd.DataFrame, train_split: float, seed: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataset into train and validation sets.

    Args:
        df: Input dataframe
        train_split: Fraction for training (rest goes to validation)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_df, val_df)
    """
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    split_idx = int(len(df) * train_split)
    return df[:split_idx], df[split_idx:]


def normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase.

    Args:
        df: Input dataframe

    Returns:
        Dataframe with normalized schema
    """
    df = df.rename(columns={"Sentence": "text", "Label": "label"})
    return df[["text", "label"]]


def process_emotions(
    raw_dir: Path,
    output_dir: Path,
    sample_fraction: float,
    train_split: float,
    random_seed: int,
) -> None:
    """Process emotion dataset: normalize, sample, and split.

    Args:
        raw_dir: Directory containing raw parquet file
        output_dir: Directory to save processed splits
        sample_fraction: Fraction of data to keep
        train_split: Fraction for training split
        random_seed: Random seed for reproducibility
    """
    train_output_dir = output_dir / "train"
    val_output_dir = output_dir / "val"
    train_output_dir.mkdir(parents=True, exist_ok=True)
    val_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Processing dataset (sampling {sample_fraction * 100:.0f}%)...")

    # Load raw data
    df = pd.read_parquet(raw_dir / "emotions.parquet")
    print(f"  Loaded {len(df)} samples")

    # Normalize schema
    df = normalize_schema(df)

    # Sample
    df = sample_data(df, sample_fraction, random_seed)
    print(f"  Sampled to {len(df)} samples")

    # Split
    train_df, val_df = split_data(df, train_split, random_seed)
    print(f"  Split: train={len(train_df)}, val={len(val_df)}")

    # Save as parquet
    train_table = pa.Table.from_pandas(train_df, preserve_index=False)
    val_table = pa.Table.from_pandas(val_df, preserve_index=False)

    pq.write_table(train_table, train_output_dir / "train.parquet")
    pq.write_table(val_table, val_output_dir / "val.parquet")

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["process"]
    process_emotions(
        raw_dir=Path(params["raw_dir"]),
        output_dir=Path(params["output_dir"]),
        sample_fraction=params["sample_fraction"],
        train_split=params["train_split"],
        random_seed=params["random_seed"],
    )
