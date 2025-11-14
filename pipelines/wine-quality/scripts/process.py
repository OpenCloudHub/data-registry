"""Convert Wine Quality CSV to clean format."""

from pathlib import Path

import pandas as pd
import yaml


def load_and_clean_wine_data(raw_dir: Path) -> pd.DataFrame:
    """Load and clean red and white wine datasets.

    Args:
        raw_dir: Directory containing raw CSV files

    Returns:
        Combined and cleaned dataframe
    """
    red_wine = pd.read_csv(raw_dir / "winequality-red.csv", sep=";")
    white_wine = pd.read_csv(raw_dir / "winequality-white.csv", sep=";")

    # Add wine type column (0=red, 1=white)
    red_wine["wine_type"] = 0
    white_wine["wine_type"] = 1

    # Combine datasets and reset index
    df = pd.concat([red_wine, white_wine], ignore_index=True)

    return df


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


def convert_to_csv(
    raw_dir: Path,
    output_dir: Path,
    sample_fraction: float = 1.0,
    random_state: int = 42,
) -> None:
    """Convert Wine Quality CSV files to single clean CSV.

    Args:
        raw_dir: Directory containing raw CSV files
        output_dir: Directory to save processed CSV file
        sample_fraction: Fraction of data to keep (default: 1.0 for full dataset)
        random_state: Random seed for reproducibility
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Processing data (sampling {sample_fraction * 100:.0f}%)...")

    # Load and clean data
    df = load_and_clean_wine_data(raw_dir)
    print(f"  Loaded {len(df)} total samples")

    # Sample if requested
    if sample_fraction < 1.0:
        df = sample_data(df, sample_fraction, random_state)
        print(f"  Sampled to {len(df)} samples")

    # Reset index to ensure clean data (no index column)
    df = df.reset_index(drop=True)

    # Save as clean CSV without index
    output_file = output_dir / "wine-quality.csv"
    df.to_csv(output_file, index=False)
    print(f"  ✓ Saved: {len(df)} samples")

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["process"]
    convert_to_csv(
        raw_dir=Path(params["raw_dir"]),
        output_dir=Path(params["output_dir"]),
        sample_fraction=params.get("sample_fraction", 1.0),
        random_state=params.get("random_state", 42),
    )
