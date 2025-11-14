"""Compute dataset metadata and statistics."""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyarrow.parquet as pq
import yaml

FEATURE_NAMES = [
    "fixed acidity",
    "volatile acidity",
    "citric acid",
    "residual sugar",
    "chlorides",
    "free sulfur dioxide",
    "total sulfur dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
    "wine_type",
]

WINE_TYPES = {0: "red", 1: "white"}


def load_split(data_path: Path) -> pd.DataFrame:
    """Load data from Parquet file.

    Args:
        data_path: Path to Parquet file

    Returns:
        DataFrame with features and quality labels
    """
    return pq.read_table(data_path).to_pandas()


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

    # Separate features and labels
    X_train = train_df.drop("quality", axis=1)
    y_train = train_df["quality"]
    X_val = val_df.drop("quality", axis=1)
    y_val = val_df["quality"]

    # Build metadata
    metadata = {
        "dataset": {
            "name": "wine-quality",
            "description": "Wine Quality dataset - physicochemical properties and quality ratings",
            "source": "https://archive.ics.uci.edu/ml/datasets/wine+quality",
            "citation": "P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis. "
            "Modeling wine preferences by data mining from physicochemical properties. "
            "Decision Support Systems, Elsevier, 47(4):547-553, 2009.",
        },
        "schema": {
            "features": {
                name: {
                    "dtype": str(X_train[name].dtype),
                    "description": f"Wine feature: {name}",
                }
                for name in X_train.columns
            },
            "target": {
                "name": "quality",
                "dtype": str(y_train.dtype),
                "description": "Wine quality score (0-10)",
                "range": [int(y_train.min()), int(y_train.max())],
            },
        },
        "splits": {
            "train": {
                "num_samples": len(train_df),
                "num_features": len(X_train.columns),
                "quality_distribution": y_train.value_counts().sort_index().to_dict(),
                "wine_type_distribution": {
                    WINE_TYPES[k]: int(v)
                    for k, v in train_df["wine_type"].value_counts().to_dict().items()
                },
            },
            "val": {
                "num_samples": len(val_df),
                "num_features": len(X_val.columns),
                "quality_distribution": y_val.value_counts().sort_index().to_dict(),
                "wine_type_distribution": {
                    WINE_TYPES[k]: int(v)
                    for k, v in val_df["wine_type"].value_counts().to_dict().items()
                },
            },
        },
        "metadata": {
            "train": {
                "features": {
                    col: {
                        "mean": float(X_train[col].mean()),
                        "std": float(X_train[col].std()),
                        "min": float(X_train[col].min()),
                        "max": float(X_train[col].max()),
                        "median": float(X_train[col].median()),
                    }
                    for col in X_train.columns
                },
                "target": {
                    "mean": float(y_train.mean()),
                    "std": float(y_train.std()),
                    "median": float(y_train.median()),
                },
            },
            "val": {
                "features": {
                    col: {
                        "mean": float(X_val[col].mean()),
                        "std": float(X_val[col].std()),
                        "min": float(X_val[col].min()),
                        "max": float(X_val[col].max()),
                        "median": float(X_val[col].median()),
                    }
                    for col in X_val.columns
                },
                "target": {
                    "mean": float(y_val.mean()),
                    "std": float(y_val.std()),
                    "median": float(y_val.median()),
                },
            },
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
    print(f"   Features: {metadata['splits']['train']['num_features']}")
    print(f"   Quality range: {metadata['schema']['target']['range']}")
