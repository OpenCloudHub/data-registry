<!-- filepath: /workspace/project/README.md -->

<a id="readme-top"></a>

<!-- PROJECT LOGO & TITLE -->

<div align="center">
  <a href="https://github.com/opencloudhub">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/opencloudhub/.github/main/assets/brand/assets/logos/primary-logo-light.svg">
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/opencloudhub/.github/main/assets/brand/assets/logos/primary-logo-dark.svg">
    <!-- Fallback -->
    <img alt="OpenCloudHub Logo" src="https://raw.githubusercontent.com/opencloudhub/.github/main/assets/brand/assets/logos/primary-logo-dark.svg" style="max-width:700px; max-height:175px;">
  </picture>
  </a>

<h1 align="center">Data Registry</h1>

<p align="center">
    Versioned datasets for reproducible ML training using DVC.<br />
    <a href="https://github.com/opencloudhub"><strong>Explore OpenCloudHub »</strong></a>
  </p>
</div>

______________________________________________________________________

<details>
  <summary>📑 Table of Contents</summary>
  <ol>
    <li><a href="#about">About</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#workflows">Workflows</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#storage-backends">Storage Backends</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

______________________________________________________________________

<h2 id="about">📊 About</h2>

This repository manages dataset preparation, versioning, and distribution for ML training pipelines. It demonstrates automated data pipelines with DVC (Data Version Control) for reproducible machine learning workflows.

**Architecture:**

```
Data Registry (DVC) → Storage (Local/MinIO) → Training Repos (Ray Data)
```

______________________________________________________________________

<h2 id="features">✨ Features</h2>

- 📊 **Automated Data Pipelines**: Download → prepare → analyze workflow
- 🔄 **Version Control**: Git tags + DVC for dataset versioning
- 📈 **Automatic Metrics**: Mean, std, distribution computation
- 🔀 **Flexible Storage**: Local devcontainer or MinIO cluster
- 🚀 **Easy Integration**: Seamless use in training repos
- 🧪 **Development Environment**: VS Code DevContainer setup

______________________________________________________________________

<h2 id="getting-started">🚀 Getting Started</h2>

### Prerequisites

- Docker
- VS Code with DevContainers extension (recommended)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/opencloudhub/data-registry.git
   cd data-registry
   ```

1. **Open in DevContainer** (Recommended)

   VSCode: `Ctrl+Shift+P` → `Dev Containers: Rebuild and Reopen in Container`

1. **Configure DVC Remote**

   **For local development:**

   ```bash
   dvc remote add -d local /workspace/shared-data/dvcstore
   dvc remote modify local mkdir true
   git add .dvc/config
   git commit -m "Configure local DVC remote"
   ```

   **For production (MinIO):**

   ```bash
   dvc remote add -d minio s3://mlops-datasets/data-registry
   dvc remote modify minio endpointurl http://minio.opencloudub.local:9000

   export AWS_ACCESS_KEY_ID=minioadmin
   export AWS_SECRET_ACCESS_KEY=minioadmin

   dvc remote default minio
   git add .dvc/config
   git commit -m "Configure MinIO remote"
   ```

### Running the Pipeline

```bash
cd src/fashion-mnist

# Run all stages
dvc repro

# Or run individually
dvc repro download
dvc repro prepare
dvc repro analyze
```

### Verifying Results

```bash
# Check pipeline status
dvc status

# View computed metrics
cat data/fashion-mnist/metrics.json

# Push to remote storage
dvc push
```

______________________________________________________________________

<h2 id="workflows">🔄 Workflows</h2>

### Data Engineer: Adding/Updating Datasets

**Create new dataset:**

```bash
# 1. Create structure
mkdir -p data/my-dataset/{raw,processed}
mkdir -p src/my-dataset/scripts

# 2. Create pipeline files (dvc.yaml, params.yaml, scripts/*.py)

# 3. Run pipeline
cd src/my-dataset
dvc repro

# 4. Version and push
dvc push
git add .
git commit -m "Add my-dataset v1.0.0"
git tag v1.0.0
git push origin main v1.0.0
```

**Update existing dataset:**

```bash
cd src/fashion-mnist
vim params.yaml  # Modify parameters
dvc repro        # Re-run pipeline
dvc push
git add . && git commit -m "Update FashionMNIST v1.1.0"
git tag v1.1.0 && git push origin main v1.1.0
```

### ML Engineer: Using Datasets

**Setup in training repo:**

```bash
pip install dvc
dvc remote add -d local /workspace/shared-data/dvcstore
```

#### Option 1: Download Data with DVC CLI

**Download specific dataset version:**

```bash
# Download to local directory
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    -o ./data/fashion-mnist \
    --rev v1.0.0

# Download just the metrics
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/metrics.json \
    -o ./data/fashion-mnist/metrics.json \
    --rev v1.0.0
```

**Import and track dataset in your repo:**

```bash
# Import creates a .dvc file to track the dataset
dvc import https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    -o data/fashion-mnist \
    --rev v1.0.0

# Later update to new version
dvc update data/fashion-mnist.dvc --rev v1.1.0
```

**Pull from configured remote:**

```bash
# If you've imported the dataset
dvc pull data/fashion-mnist.dvc
```

#### Option 2: Load Data in Python Code

**Load data in training code:**

```python
import dvc.api
import ray
import json


def load_versioned_data(dataset_name, version="v1.0.0"):
    """Load specific dataset version."""
    repo = "https://github.com/OpenCloudHub/data-registry"

    train_path = dvc.api.get_url(
        f"data/{dataset_name}/processed/train.parquet", repo=repo, rev=version
    )
    val_path = dvc.api.get_url(
        f"data/{dataset_name}/processed/val.parquet", repo=repo, rev=version
    )

    metrics_content = dvc.api.read(
        f"data/{dataset_name}/metrics.json", repo=repo, rev=version
    )
    metrics = json.loads(metrics_content)

    train_ds = ray.data.read_parquet(train_path)
    val_ds = ray.data.read_parquet(val_path)

    return train_ds, val_ds, metrics


# Usage
train_ds, val_ds, metrics = load_versioned_data("fashion-mnist", "v1.0.0")

# Log to MLflow
import mlflow

mlflow.log_params(
    {
        "data_version": "v1.0.0",
        "data_pixel_mean": metrics["pixel_mean"],
        "data_pixel_std": metrics["pixel_std"],
    }
)
```

______________________________________________________________________

<h2 id="project-structure">📁 Project Structure</h2>

```
data-registry/
├── data/
│   └── fashion-mnist/
│       ├── raw/                # Downloaded files (DVC-tracked)
│       ├── processed/          # Parquet files (DVC-tracked)
│       └── metrics.json        # Dataset metrics (git-tracked)
├── src/
│   └── fashion-mnist/
│       ├── dvc.yaml           # Pipeline definition
│       ├── params.yaml        # Pipeline parameters
│       └── scripts/
│           ├── download.py    # Stage 1: Download raw data
│           ├── prepare.py     # Stage 2: Convert to Parquet
│           └── analyze.py     # Stage 3: Compute metrics
├── .devcontainer/             # VS Code DevContainer config
├── .dvc/
│   └── config                 # DVC remote configuration
└── .github/workflows/         # CI/CD workflows (future)
```

______________________________________________________________________

<h2 id="storage-backends">💾 Storage Backends</h2>

### Local Shared Storage (Development)

Make sure the mounted path exists locally and that you adjust the name in the
[devcontainer.json](.devcontainer/devcontainer.json) `mounts` section.

**Configuration:**

```
Host: ~Development/projects/opencloudub/dev/shared-data/dvcstore/
Container: /workspace/shared-data/dvcstore/
```

**Benefits:** Fast, no infrastructure, shared across devcontainers\
**Limitations:** Single machine only, no backup

### MinIO (Production)

**Configuration:**

```bash
dvc remote add -d minio s3://mlops-datasets/data-registry
dvc remote modify minio endpointurl http://minio.opencloudub.local:9000
```

**Benefits:** Centralized, accessible across cluster, production-ready\
**Use:** Set credentials via environment variables

### Switching Between Remotes

```bash
# List remotes
dvc remote list

# Switch default
dvc remote default local   # For dev
dvc remote default minio   # For production

# Push to specific remote
dvc push -r minio
```

______________________________________________________________________

<h2 id="contributing">👥 Contributing</h2>

Contributions are welcome! This project follows OpenCloudHub's contribution standards.

Please see our [Contributing Guidelines](https://github.com/opencloudhub/.github/blob/main/.github/CONTRIBUTING.md) and [Code of Conduct](https://github.com/opencloudhub/.github/blob/main/.github/CODE_OF_CONDUCT.md) for more details.

______________________________________________________________________

<h2 id="license">📄 License</h2>

Distributed under the Apache 2.0 License. See [LICENSE](LICENSE) for more information.

______________________________________________________________________

<h2 id="contact">📬 Contact</h2>

Organization Link: [https://github.com/OpenCloudHub](https://github.com/OpenCloudHub)

Project Link: [https://github.com/opencloudhub/data-registry](https://github.com/opencloudhub/data-registry)

______________________________________________________________________

<h2 id="acknowledgements">🙏 Acknowledgements</h2>

- [DVC](https://dvc.org/) - Data version control
- [Ray Data](https://docs.ray.io/en/latest/data/data.html) - Distributed data loading
- [MinIO](https://min.io/) - S3-compatible object storage
- [MLflow](https://mlflow.org/) - ML lifecycle management

<p align="right">(<a href="#readme-top">back to top</a>)</p>
