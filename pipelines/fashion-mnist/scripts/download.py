# src/fashion-mnist/scripts/download.py
"""Download FashionMNIST."""

import urllib.request
from pathlib import Path

import yaml

params = yaml.safe_load(open("params.yaml"))["download"]
base_url = params.get(
    "base_url", "http://fashion-mnist.s3-website.eu-central-1.amazonaws.com"
)
output_dir = Path(params["output_dir"])
output_dir.mkdir(parents=True, exist_ok=True)

files = [
    "train-images-idx3-ubyte.gz",
    "train-labels-idx1-ubyte.gz",
    "t10k-images-idx3-ubyte.gz",
    "t10k-labels-idx1-ubyte.gz",
]

print(f"📥 Downloading FashionMNIST from {base_url}...")
for filename in files:
    filepath = output_dir / filename
    print(f"  Downloading {filename}...")
    urllib.request.urlretrieve(f"{base_url}/{filename}", filepath)

print("✅ Done")
