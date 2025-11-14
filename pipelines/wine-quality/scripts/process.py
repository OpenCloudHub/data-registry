"""Convert Wine Quality CSV to Parquet."""

from pathlib import Path
from typing import Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from sklearn.model_selection import train_test_split


def load_wine_data(raw_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load red and white wine datasets.

    Args:
        raw_dir: Directory containing raw CSV files

    Returns:
        Tuple of (red_wine_df, white_wine_df)
    """
    red_wine = pd.read_csv(raw_dir / "winequality-red.csv", sep=";")
    white_wine = pd.read_csv(raw_dir / "winequality-white.csv", sep=";")

    # Add wine type column
    red_wine["wine_type"] = 0  # Red
    white_wine["wine_type"] = 1  # White

    return red_wine, white_wine


def sample_data(
    df: pd.DataFrame, fraction: float, random_state: int = 42
) -> pd.DataFrame:
    """Sample a fraction of the dataset.

    Args:
        df: Input dataframe
        fraction: Fraction of data to keep (0.0 to 1.0)
        random_state: Random seed for reproducibility

    Returns:
        Sampled dataframe
    """
    if fraction >= 1.0:
        return df

    n_samples = int(len(df) * fraction)
    return df.sample(n=n_samples, random_state=random_state).reset_index(drop=True)


def convert_to_parquet(
    raw_dir: Path,
    output_dir: Path,
    sample_fraction: float = 1.0,
    test_size: float = 0.2,
    random_state: int = 42,
) -> None:
    """Convert Wine Quality CSV files to Parquet format.

    Args:
        raw_dir: Directory containing raw CSV files
        output_dir: Directory to save Parquet files
        sample_fraction: Fraction of data to keep (default: 1.0 for full dataset)
        test_size: Proportion for test/validation split
        random_state: Random seed for reproducibility
    """
    train_output_dir = output_dir / "train"
    val_output_dir = output_dir / "val"
    train_output_dir.mkdir(parents=True, exist_ok=True)
    val_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Converting to Parquet (sampling {sample_fraction * 100:.0f}%)...")

    # Load both red and white wine datasets
    red_wine, white_wine = load_wine_data(raw_dir)

    # Combine datasets
    df = pd.concat([red_wine, white_wine], ignore_index=True)
    print(
        f"  Loaded {len(red_wine)} red + {len(white_wine)} white = {len(df)} total samples"
    )

    # Sample if requested
    if sample_fraction < 1.0:
        df = sample_data(df, sample_fraction, random_state)
        print(f"  Sampled to {len(df)} samples")

    # Split features and target
    X = df.drop("quality", axis=1)
    y = df["quality"]

    # Train/val split with stratification
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Save as Parquet
    train_df = X_train.copy()
    train_df["quality"] = y_train
    pq.write_table(pa.Table.from_pandas(train_df), train_output_dir / "train.parquet")
    print(f"  ✓ train: {len(train_df)} samples")

    val_df = X_val.copy()
    val_df["quality"] = y_val
    pq.write_table(pa.Table.from_pandas(val_df), val_output_dir / "val.parquet")
    print(f"  ✓ val: {len(val_df)} samples")

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["process"]
    convert_to_parquet(
        raw_dir=Path(params["raw_dir"]),
        output_dir=Path(params["output_dir"]),
        sample_fraction=params.get("sample_fraction", 1.0),
        test_size=params.get("test_size", 0.2),
        random_state=params.get("random_state", 42),
    )
