# src/fashion-mnist/scripts/analyze.py
"""Compute metrics."""

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import yaml

params = yaml.safe_load(open("params.yaml"))["analyze"]
data_dir = Path(params["data_dir"])
output_file = Path(params["output_file"])

print("📊 Computing metrics...")

# Load train data
table = pq.read_table(data_dir / "train" / "train.parquet")
images = np.array(table["image"].to_pylist(), dtype=np.uint8) / 255.0
labels = np.array(table["label"].to_pylist())

# Compute stats
metrics = {
    "pixel_mean": float(images.mean()),
    "pixel_std": float(images.std()),
    "train_samples": len(images),
    "class_distribution": np.bincount(labels, minlength=10).tolist(),
}

# Save
output_file.parent.mkdir(parents=True, exist_ok=True)
json.dump(metrics, open(output_file, "w"), indent=2)

print(f"✅ Saved to {output_file}")
print(f"   mean={metrics['pixel_mean']:.4f}, std={metrics['pixel_std']:.4f}")
