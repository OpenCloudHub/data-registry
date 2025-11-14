"""Compute dataset metadata and statistics."""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import numpy.typing as npt
import pyarrow.parquet as pq
import yaml

CLASS_NAMES = [
    "T-shirt/top",
    "Trouser",
    "Pullover",
    "Dress",
    "Coat",
    "Sandal",
    "Shirt",
    "Sneaker",
    "Bag",
    "Ankle boot",
]


def load_split(
    data_path: Path,
) -> Tuple[npt.NDArray[np.uint8], npt.NDArray[np.uint8]]:
    """Load images and labels from Parquet file.

    Args:
        data_path: Path to Parquet file

    Returns:
        Tuple of (images, labels)
    """
    table = pq.read_table(data_path)
    images = np.array(table["image"].to_pylist(), dtype=np.uint8)
    labels = np.array(table["label"].to_pylist(), dtype=np.uint8)
    return images, labels


def compute_metadata(data_dir: Path) -> Dict[str, Any]:
    """Compute comprehensive dataset metadata.

    Args:
        data_dir: Directory containing processed data splits

    Returns:
        Dictionary containing all metadata
    """
    # Load data
    train_images, train_labels = load_split(data_dir / "train" / "train.parquet")
    val_images, val_labels = load_split(data_dir / "val" / "val.parquet")

    # Normalize for statistics
    train_norm = train_images / 255.0
    val_norm = val_images / 255.0

    # Build metadata
    metadata = {
        "dataset": {
            "name": "fashion-mnist",
            "description": "Fashion-MNIST dataset - grayscale images of fashion items",
            "source": "http://fashion-mnist.s3-website.eu-central-1.amazonaws.com",
        },
        "schema": {
            "features": {
                "image": {
                    "dtype": "uint8",
                    "shape": list(train_images.shape[1:]),
                    "description": "28x28 grayscale image",
                },
                "label": {
                    "dtype": "uint8",
                    "shape": [],
                    "description": "Class label (0-9)",
                    "classes": {str(i): name for i, name in enumerate(CLASS_NAMES)},
                },
            }
        },
        "splits": {
            "train": {
                "num_samples": len(train_images),
                "num_features": 2,
                "class_distribution": {
                    CLASS_NAMES[i]: int(count)
                    for i, count in enumerate(np.bincount(train_labels, minlength=10))
                },
            },
            "val": {
                "num_samples": len(val_images),
                "num_features": 2,
                "class_distribution": {
                    CLASS_NAMES[i]: int(count)
                    for i, count in enumerate(np.bincount(val_labels, minlength=10))
                },
            },
        },
        "statistics": {
            "train": {
                "pixel_mean": float(train_norm.mean()),
                "pixel_std": float(train_norm.std()),
                "pixel_min": float(train_norm.min()),
                "pixel_max": float(train_norm.max()),
                "pixel_median": float(np.median(train_norm)),
            },
            "val": {
                "pixel_mean": float(val_norm.mean()),
                "pixel_std": float(val_norm.std()),
                "pixel_min": float(val_norm.min()),
                "pixel_max": float(val_norm.max()),
                "pixel_median": float(np.median(val_norm)),
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
    print(f"   Shape: {metadata['schema']['features']['image']['shape']}")
    print(
        f"   Train stats: mean={metadata['statistics']['train']['pixel_mean']:.4f}, "
        f"std={metadata['statistics']['train']['pixel_std']:.4f}"
    )
