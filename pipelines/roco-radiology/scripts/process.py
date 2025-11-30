#!/usr/bin/env python3
"""Process raw radiology data to Qwen format."""

import json
import os
from pathlib import Path
from shutil import copy2

import mlflow
import yaml


def load_prompt_from_mlflow(prompt_name: str, version: int) -> tuple[str, dict]:
    """Load prompt from MLflow registry."""
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))

    prompt_uri = f"prompts:/{prompt_name}/{version}"
    print(f"📝 Loading prompt: {prompt_uri}")

    prompt = mlflow.genai.load_prompt(prompt_uri)

    metadata = {
        "prompt_name": prompt_name,
        "prompt_version": version,
        "prompt_uri": prompt_uri,
        "prompt_text": prompt.template,
    }

    return prompt.template, metadata


def process_to_qwen_format(
    raw_dir: Path,
    output_dir: Path,
    stats_file: Path,
    train_split: float,
    prompt_name: str,
    prompt_version: int,
) -> dict:
    """Convert raw dataset to Qwen conversation format."""

    # Load prompt from MLflow
    instruction, prompt_metadata = load_prompt_from_mlflow(prompt_name, prompt_version)

    # Setup directories
    train_dir = output_dir / "train"
    test_dir = output_dir / "test"
    train_images = train_dir / "images"
    test_images = test_dir / "images"

    train_images.mkdir(parents=True, exist_ok=True)
    test_images.mkdir(parents=True, exist_ok=True)

    # Load raw captions
    print(f"📦 Loading raw data from {raw_dir}...")
    with open(raw_dir / "captions.json") as f:
        raw_data = json.load(f)

    raw_images_dir = raw_dir / "images"

    split_idx = int(len(raw_data) * train_split)
    train_data = []
    test_data = []

    print(f"🔄 Processing {len(raw_data)} samples with prompt V{prompt_version}...")

    for i, sample in enumerate(raw_data):
        is_train = i < split_idx
        images_dir = train_images if is_train else test_images
        prefix = "train" if is_train else "test"

        # Copy image with new name
        src_image = raw_images_dir / sample["image"]
        new_filename = f"{prefix}_radiology_{i:06d}.jpg"
        dst_image = images_dir / new_filename

        copy2(src_image, dst_image)

        # Create annotation
        annotation = {
            "image": new_filename,
            "conversations": [
                {"from": "human", "value": f"<image>\n{instruction}"},
                {"from": "gpt", "value": sample["caption"]},
            ],
        }

        if is_train:
            train_data.append(annotation)
        else:
            test_data.append(annotation)

        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1}/{len(raw_data)}")

    # Save annotations
    with open(train_dir / "annotations.json", "w") as f:
        json.dump(train_data, f, indent=2)

    with open(test_dir / "annotations.json", "w") as f:
        json.dump(test_data, f, indent=2)

    # Save process stats
    stats = {
        "train_samples": len(train_data),
        "test_samples": len(test_data),
        "train_split": train_split,
        "prompt": prompt_metadata,
    }

    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"✅ Created {len(train_data)} train + {len(test_data)} test samples")
    print(f"📊 Saved stats to {stats_file}")

    return stats


if __name__ == "__main__":
    params = yaml.safe_load(open("params.yaml"))["process"]

    process_to_qwen_format(
        raw_dir=Path(params["raw_dir"]),
        output_dir=Path(params["output_dir"]),
        stats_file=Path(params["stats_file"]),
        train_split=params["train_split"],
        prompt_name=params["prompt_name"],
        prompt_version=params["prompt_version"],
    )
