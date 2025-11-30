#!/usr/bin/env python3
"""Compute radiology dataset metadata and statistics."""

import json
from pathlib import Path

import yaml
from PIL import Image


def compute_metadata(data_dir: Path, stats_file: Path) -> dict:
    """Compute dataset metadata including prompt info from process stats."""

    # Load process stats
    with open(stats_file) as f:
        process_stats = json.load(f)

    metadata = {
        "dataset": {
            "name": "radiology-mini",
            "description": "Medical radiology images with captions for VLM fine-tuning",
            "source": "unsloth/Radiology_mini",
            "format": "Qwen conversation format",
        },
        "prompt": process_stats.get("prompt", {}),
        "splits": {},
        "metrics": {},
    }

    for split in ["train", "test"]:
        split_dir = data_dir / split
        annotations_path = split_dir / "annotations.json"
        images_dir = split_dir / "images"

        with open(annotations_path) as f:
            annotations = json.load(f)

        # Caption stats
        caption_lengths = [
            len(ann["conversations"][1]["value"].split()) for ann in annotations
        ]

        # Image stats (sample first 100)
        image_sizes = []
        for ann in annotations[:100]:
            img_path = images_dir / ann["image"]
            if img_path.exists():
                with Image.open(img_path) as img:
                    image_sizes.append((img.width, img.height))

        metadata["splits"][split] = {
            "num_samples": len(annotations),
        }

        metadata["metrics"][split] = {
            "caption_length_mean": round(
                sum(caption_lengths) / len(caption_lengths), 2
            ),
            "caption_length_min": min(caption_lengths),
            "caption_length_max": max(caption_lengths),
            "image_width_mean": round(
                sum(w for w, h in image_sizes) / len(image_sizes), 2
            )
            if image_sizes
            else 0,
            "image_height_mean": round(
                sum(h for w, h in image_sizes) / len(image_sizes), 2
            )
            if image_sizes
            else 0,
        }

    return metadata


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["analyze"]

    print("📊 Computing dataset metadata...")
    metadata = compute_metadata(
        data_dir=Path(params["data_dir"]),
        stats_file=Path(params["stats_file"]),
    )

    output_file = Path(params["output_file"])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Saved metadata to {output_file}")
    print(f"   Train: {metadata['splits']['train']['num_samples']} samples")
    print(f"   Test: {metadata['splits']['test']['num_samples']} samples")
    if metadata.get("prompt"):
        print(
            f"   Prompt: {metadata['prompt']['prompt_name']} v{metadata['prompt']['prompt_version']}"
        )
