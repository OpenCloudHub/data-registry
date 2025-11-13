# src/fashion-mnist/scripts/process.py
"""Convert IDX to Parquet."""

import gzip
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

params = yaml.safe_load(open("params.yaml"))["process"]
raw_dir = Path(params["raw_dir"])
output_dir = Path(params["output_dir"])
output_dir_train = output_dir / "train"
output_dir_val = output_dir / "val"
output_dir_train.mkdir(parents=True, exist_ok=True)
output_dir_val.mkdir(parents=True, exist_ok=True)


def read_idx(images_gz, labels_gz):
    """Read IDX files, return images and labels."""
    with gzip.open(images_gz, "rb") as f:
        f.read(16)  # Skip header
        images = np.frombuffer(f.read(), dtype=np.uint8).reshape(-1, 28, 28)

    with gzip.open(labels_gz, "rb") as f:
        f.read(8)  # Skip header
        labels = np.frombuffer(f.read(), dtype=np.uint8)

    return images, labels


print("📦 Converting to Parquet...")

# Train
images, labels = read_idx(
    raw_dir / "train-images-idx3-ubyte.gz", raw_dir / "train-labels-idx1-ubyte.gz"
)
table = pa.table({"image": images.reshape(-1, 784).tolist(), "label": labels})
pq.write_table(table, output_dir_train / "train.parquet")
print(f"  ✓ train: {len(images)} samples")

# Val
images, labels = read_idx(
    raw_dir / "t10k-images-idx3-ubyte.gz", raw_dir / "t10k-labels-idx1-ubyte.gz"
)
table = pa.table({"image": images.reshape(-1, 784).tolist(), "label": labels})
pq.write_table(table, output_dir_val / "val.parquet")
print(f"  ✓ val: {len(images)} samples")

print("✅ Done")
