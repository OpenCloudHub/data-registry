# ==============================================================================
# Fashion-MNIST Dataset Downloader
# ==============================================================================
#
# Downloads the Fashion-MNIST dataset from the official source.
# Fashion-MNIST is a drop-in replacement for MNIST with 10 fashion categories.
#
# Dataset Info:
#   - 60,000 training images + 10,000 test images
#   - 28x28 grayscale images
#   - 10 classes: T-shirt, Trouser, Pullover, Dress, Coat, Sandal, Shirt,
#                 Sneaker, Bag, Ankle boot
#
# Output Files (IDX format, gzipped):
#   - train-images-idx3-ubyte.gz
#   - train-labels-idx1-ubyte.gz
#   - t10k-images-idx3-ubyte.gz
#   - t10k-labels-idx1-ubyte.gz
#
# Usage:
#   python scripts/download.py
#
# Configuration:
#   See params.yaml for base_url and output_dir settings.
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Download FashionMNIST dataset."""

import urllib.request
from pathlib import Path

import yaml


def download_fashion_mnist(base_url: str, output_dir: Path) -> None:
    """Download FashionMNIST dataset files.

    Args:
        base_url: Base URL for the dataset
        output_dir: Directory to save downloaded files
    """
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
        url = f"{base_url}/{filename}"
        print(f"  Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)

    print("✅ Done")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["download"]
    download_fashion_mnist(
        base_url=params["base_url"],
        output_dir=Path(params["output_dir"]),
    )
