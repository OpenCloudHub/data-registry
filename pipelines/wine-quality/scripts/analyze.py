"""Compute dataset metadata and statistics."""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

WINE_TYPES = {0: "red", 1: "white"}


def compute_metadata(data_dir: Path) -> Dict[str, Any]:
    """Compute comprehensive dataset metadata.

    Args:
        data_dir: Directory containing processed data file

    Returns:
        Dictionary containing all metadata
    """
    # Load data
    df = pd.read_csv(data_dir / "wine-quality.csv")

    # Separate features and labels
    X = df.drop("quality", axis=1)
    y = df["quality"]

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
                    "dtype": str(X[name].dtype),
                    "description": f"Wine feature: {name}",
                }
                for name in X.columns
            },
            "target": {
                "name": "quality",
                "dtype": str(y.dtype),
                "description": "Wine quality score (0-10)",
                "range": [int(y.min()), int(y.max())],
            },
        },
        "summary": {
            "num_samples": len(df),
            "num_features": len(X.columns),
            "quality_distribution": {
                int(k): int(v)
                for k, v in y.value_counts().sort_index().to_dict().items()
            },
            "wine_type_distribution": {
                WINE_TYPES[int(k)]: int(v)
                for k, v in df["wine_type"].value_counts().to_dict().items()
            },
        },
        "statistics": {
            "features": {
                col: {
                    "mean": float(X[col].mean()),
                    "std": float(X[col].std()),
                    "min": float(X[col].min()),
                    "max": float(X[col].max()),
                    "median": float(X[col].median()),
                }
                for col in X.columns
            },
            "target": {
                "mean": float(y.mean()),
                "std": float(y.std()),
                "median": float(y.median()),
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
    print(f"   Total samples: {metadata['summary']['num_samples']}")
    print(f"   Features: {metadata['summary']['num_features']}")
    print(f"   Quality range: {metadata['schema']['target']['range']}")
