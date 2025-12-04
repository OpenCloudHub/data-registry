#!/usr/bin/env python3
# ==============================================================================
# Radiology Dataset Downloader (ROCO Mini)
# ==============================================================================
#
# Downloads medical radiology images with captions from HuggingFace.
# Used for Vision-Language Model (VLM) fine-tuning demonstrations.
#
# Dataset: unsloth/Radiology_mini
#   - Medical X-ray and CT images
#   - Natural language captions describing findings
#   - Suitable for medical VLM training (Qwen-VL, LLaVA, etc.)
#
# Output Structure:
#   raw/
#   ├── images/
#   │   ├── image_000000.jpg
#   │   ├── image_000001.jpg
#   │   └── ...
#   └── captions.json
#
# Configuration:
#   - num_samples in params.yaml limits download size for demos
#   - Images converted to RGB JPEG for consistency
#
# Usage:
#   python scripts/download.py
#
# Part of the Data Registry MLOps Demo - Thesis Project
# ==============================================================================

"""Download Radiology dataset from HuggingFace."""

from pathlib import Path

import yaml
from datasets import load_dataset


def download_radiology(
    dataset_name: str, output_dir: Path, num_samples: int | None = None
) -> None:
    """Download radiology dataset and save images + captions.

    Args:
        dataset_name: HuggingFace dataset name
        output_dir: Directory to save raw data
        num_samples: Limit samples (None for all)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 Downloading {dataset_name}...")
    dataset = load_dataset(dataset_name, split="train")

    if num_samples:
        dataset = dataset.select(range(min(num_samples, len(dataset))))

    # Save images and captions separately (DVC-friendly)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    captions = []
    print(f"💾 Saving {len(dataset)} samples...")

    for i, sample in enumerate(dataset):
        # Save image
        image_filename = f"image_{i:06d}.jpg"
        image_path = images_dir / image_filename

        image = sample["image"]
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(image_path, "JPEG", quality=95)

        # Collect caption
        captions.append(
            {
                "image": image_filename,
                "caption": sample["caption"],
            }
        )

        if (i + 1) % 500 == 0:
            print(f"  Saved {i + 1}/{len(dataset)}")

    # Save captions as JSON
    import json

    captions_path = output_dir / "captions.json"
    with open(captions_path, "w") as f:
        json.dump(captions, f, indent=2)

    print(f"✅ Downloaded {len(dataset)} samples to {output_dir}")
    print(f"   Images: {images_dir}")
    print(f"   Captions: {captions_path}")


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["download"]
    download_radiology(
        dataset_name=params["dataset_name"],
        output_dir=Path(params["output_dir"]),
        num_samples=params.get("num_samples"),
    )
