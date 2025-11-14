"""Convert IDX format to Parquet."""

import gzip
from pathlib import Path
from typing import Tuple

import numpy as np
import numpy.typing as npt
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


def read_idx(
    images_path: Path, labels_path: Path
) -> Tuple[npt.NDArray[np.uint8], npt.NDArray[np.uint8]]:
    """Read IDX files and return images and labels.

    Args:
        images_path: Path to gzipped IDX images file
        labels_path: Path to gzipped IDX labels file

    Returns:
        Tuple of (images, labels) where images have shape (N, 28, 28)
    """
    with gzip.open(images_path, "rb") as f:
        f.read(16)  # Skip header
        images = np.frombuffer(f.read(), dtype=np.uint8).reshape(-1, 28, 28)

    with gzip.open(labels_path, "rb") as f:
        f.read(8)  # Skip header
        labels = np.frombuffer(f.read(), dtype=np.uint8)

    return images, labels


def sample_data(
    images: npt.NDArray[np.uint8],
    labels: npt.NDArray[np.uint8],
    fraction: float,
) -> Tuple[npt.NDArray[np.uint8], npt.NDArray[np.uint8]]:
    """Sample a fraction of the dataset with reproducible randomness.

    Args:
        images: Image array
        labels: Label array
        fraction: Fraction of data to keep (0.0 to 1.0)

    Returns:
        Tuple of (sampled_images, sampled_labels)
    """
    if fraction >= 1.0:
        return images, labels

    n_samples = int(len(images) * fraction)
    rng = np.random.RandomState(42)
    indices = rng.choice(len(images), n_samples, replace=False)
    return images[indices], labels[indices]


def convert_to_parquet(
    raw_dir: Path, output_dir: Path, sample_fraction: float = 1.0
) -> None:
    """Convert FashionMNIST IDX files to Parquet format.

    Args:
        raw_dir: Directory containing raw IDX files
        output_dir: Directory to save Parquet files
        sample_fraction: Fraction of data to keep (default: 1.0 for full dataset)
    """
    train_output_dir = output_dir / "train"
    val_output_dir = output_dir / "val"
    train_output_dir.mkdir(parents=True, exist_ok=True)
    val_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Converting to Parquet (sampling {sample_fraction * 100:.0f}%)...")

    # Train split
    images, labels = read_idx(
        raw_dir / "train-images-idx3-ubyte.gz",
        raw_dir / "train-labels-idx1-ubyte.gz",
    )
    images, labels = sample_data(images, labels, sample_fraction)
    table = pa.table({"image": images.tolist(), "label": labels})
    pq.write_table(table, train_output_dir / "train.parquet")
    print(f"  ✓ train: {len(images)} samples")

    # Val split
    images, labels = read_idx(
        raw_dir / "t10k-images-idx3-ubyte.gz",
        raw_dir / "t10k-labels-idx1-ubyte.gz",
    )
    images, labels = sample_data(images, labels, sample_fraction)
    table = pa.table({"image": images.tolist(), "label": labels})
    pq.write_table(table, val_output_dir / "val.parquet")
    print(f"  ✓ val: {len(images)} samples")

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["process"]
    convert_to_parquet(
        raw_dir=Path(params["raw_dir"]),
        output_dir=Path(params["output_dir"]),
        sample_fraction=params.get("sample_fraction", 1.0),
    )
