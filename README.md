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

<h1 align="center">Data Registry MLOps Demo</h1>

<p align="center">
    Versioned datasets for reproducible ML training using <a href="https://dvc.org/"><medium>DVC</medium></a>.<br />
    <a href="https://github.com/opencloudhub"><strong>Explore OpenCloudHub »</strong></a>
  </p>
</div>

______________________________________________________________________

<details>
  <summary>📑 Table of Contents</summary>
  <ol>
    <li><a href="#about">About</a></li>
    <li><a href="#why-dvc">Why DVC</a></li>
    <li><a href="#available-datasets">Available Datasets</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#workflows">Workflows</a></li>
    <li><a href="#production-architecture">Production Architecture</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#storage-backends">Storage Backends</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

______________________________________________________________________

<h2 id="about">📊 About</h2>

This repository manages dataset preparation, versioning, and distribution for ML training pipelines. It demonstrates automated data pipelines with [DVC](https://dvc.org/) (Data Version Control) for reproducible machine learning workflows.

**Architecture:**

```
Data Registry (DVC) → Storage (Local/MinIO) → Training Repos (Ray Data)
       ↓                                              ↓
   Git Tags (e.g., fashion-mnist-v1.0.0)    →    MLflow Tracking
```

______________________________________________________________________

<h2 id="why-dvc">🤔 Why DVC?</h2>

> *"What exact samples were in the training data for model v2.3 that we deployed two weeks ago?"*

DVC (Data Version Control) answers this question. It solves a fundamental problem in ML: **tracking which exact data was used to train a model**.

### The Problem

- Raw data changes over time (new samples, corrections, augmentations)
- Training results become unreproducible
- No way to rollback to a known-good dataset state
- Large files don't belong in Git

### The Solution

DVC creates **git-like versioning for data**:

```bash
# Data versions are tied to git tags
git tag fashion-mnist-v1.0.0   # Points to specific dvc.lock
git tag fashion-mnist-v1.1.0   # New data version

# Training code references exact version
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    --rev fashion-mnist-v1.0.0
```

### Data Lineage Through the ML Lifecycle

The data version tag flows through the entire ML pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA REGISTRY                             │
│  fashion-mnist-v1.0.0 → MinIO (s3://dvcstore/files/md5/...)     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      TRAINING JOB                                │
│  Input: data_version=fashion-mnist-v1.0.0                       │
│  Output: model artifact + MLflow run                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       MLFLOW TRACKING                            │
│  Params:                                                         │
│    - data_version: fashion-mnist-v1.0.0                         │
│    - data_pixel_mean: 0.2860                                    │
│    - data_pixel_std: 0.3530                                     │
│  → Full reproducibility: same data + same code = same model     │
└─────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

<h2 id="available-datasets">📦 Available Datasets</h2>

| Dataset                           | Description                        | Format                    | Use Case                     |
| --------------------------------- | ---------------------------------- | ------------------------- | ---------------------------- |
| `fashion-mnist`                   | Fashion product images             | Parquet (images + labels) | Image classification         |
| `emotion`                         | Text emotion dataset               | Parquet (text + labels)   | Text classification          |
| `wine-quality`                    | Wine quality ratings               | CSV                       | Tabular regression           |
| `radiology-mini`                  | Medical X-ray images with captions | Images + JSON annotations | Vision-Language Models (VLM) |
| `opencloudhub-readmes`            | Repository README files            | Markdown files            | RAG / Embeddings             |
| `opencloudhub-readmes-embeddings` | Vectorized READMEs                 | pgvector database         | Semantic search              |

______________________________________________________________________

<h2 id="features">✨ Features</h2>

- 📊 **Automated Data Pipelines**: Download → process → analyze workflow
- 🔄 **Version Control**: Git tags + DVC for dataset versioning
- 📈 **Automatic Metrics**: Statistics computed and tracked per dataset
- 🔀 **Flexible Storage**: Local Docker Compose or MinIO cluster
- 🚀 **Easy Integration**: Seamless use in training repos via `dvc get` or Python API
- ☸️ **Production Patterns**: GitHub Actions + Argo Workflows for cluster execution
- ⚡ **Ray Data Integration**: Distributed processing for large datasets
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

1. **Configure environment**

   **For local Docker Compose setup:**

   ```bash
   # Source environment variables
   set -a && source .env.docker && set +a

   # DVC is pre-configured to use local remote pointing to MinIO
   dvc remote default local
   ```

   **For Minikube/Kubernetes setup:**

   ```bash
   set -a && source .env.minikube && set +a
   dvc remote default minio
   ```

### Running a Pipeline Locally

```bash
cd pipelines/fashion-mnist

# Run all stages
dvc repro

# Or run individually
dvc repro download
dvc repro process
dvc repro analyze

# Bootstrap all pipelines locally with version 1.0.0 for all
bash /workspace/project/scripts/bootstrap-data-examples.sh
```

### Verifying Results

```bash
# Check pipeline status
dvc status

# View computed metadata
cat data/fashion-mnist/metadata.json

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
mkdir -p pipelines/my-dataset/scripts

# 2. Create pipeline files (dvc.yaml, params.yaml, scripts/*.py)

# 3. Run pipeline
cd pipelines/my-dataset
dvc repro

# 4. Version and push
dvc push
git add .
git commit -m "Add my-dataset v1.0.0"
git tag my-dataset-v1.0.0
git push origin main my-dataset-v1.0.0
```

### ML Engineer: Using Datasets

#### Option 1: Download with DVC CLI

```bash
# Download specific dataset version
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    -o ./data/fashion-mnist \
    --rev fashion-mnist-v1.0.0

# Download radiology dataset for VLM training
dvc get https://github.com/OpenCloudHub/data-registry \
    data/radiology-mini/processed \
    -o ./data/radiology-mini \
    --rev radiology-mini-v1.0.0
```

#### Option 2: Python API (Recommended for Training Code)

```python
import dvc.api
import json

REPO = "https://github.com/OpenCloudHub/data-registry"
VERSION = "fashion-mnist-v1.0.0"

# Get S3 URLs for direct loading with Ray Data
train_url = dvc.api.get_url(
    "data/fashion-mnist/processed/train/train.parquet", repo=REPO, rev=VERSION
)

# Load metadata for normalization params
metadata = json.loads(
    dvc.api.read("data/fashion-mnist/metadata.json", repo=REPO, rev=VERSION)
)

# Log to MLflow for reproducibility
import mlflow

mlflow.log_params(
    {
        "data_version": VERSION,
        "data_pixel_mean": metadata["metrics"]["train"]["pixel_mean"],
    }
)
```

#### Option 3: Ray Data Integration

```python
import ray
import dvc.api
import s3fs

# Get URLs from DVC
train_url = dvc.api.get_url(
    "data/radiology-mini/processed/train", repo=REPO, rev="radiology-mini-v1.0.0"
)

# Create S3 filesystem for MinIO
fs = s3fs.S3FileSystem(
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    key=os.getenv("AWS_ACCESS_KEY_ID"),
    secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# Load with Ray Data for distributed processing
ds = ray.data.read_images(train_url, filesystem=fs)
```

______________________________________________________________________

<h2 id="production-architecture">🏭 Production Architecture</h2>

In production, pipelines run on a Kubernetes cluster via GitHub Actions and Argo Workflows—not manually.

### Pipeline Execution Options

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXECUTION OPTIONS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. LOCAL (Development)                                         │
│     └─ dvc repro pipelines/fashion-mnist/dvc.yaml               │
│                                                                  │
│  2. GITHUB ACTIONS → ARGO WORKFLOWS (Production)                │
│     └─ Trigger via workflow_dispatch or schedule                │
│     └─ Submits to Argo Workflow on cluster                      │
│                                                                  │
│  3. RAY DATA (Distributed Processing)                           │
│     └─ For compute-heavy pipelines (embeddings, large datasets) │
│     └─ Scales across Ray cluster workers                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### GitHub Actions Integration

Pipelines are triggered via GitHub Actions which submit jobs to the cluster:

```yaml
# .github/workflows/run-data-pipelines.yaml
on:
  workflow_dispatch:
    inputs:
      pipelines:
        description: 'Pipelines to run (comma-separated)'
        default: 'opencloudhub-readmes-download,fashion-mnist'
  schedule:
    - cron: '0 2 * * *'  # Nightly automated runs
```

The workflow submits an Argo Workflow that:

1. Clones the repo
1. Runs `dvc repro` for each pipeline
1. Pushes data to MinIO
1. Auto-tags with semantic versioning (e.g., `fashion-mnist-v1.2.3`)
1. Commits updated `dvc.lock` files

### Argo Workflow Templates

We maintain reusable workflow templates in the [gitops repo](https://github.com/OpenCloudHub/gitops/tree/main/src/platform/mlops/argo-workflows/workflow-templates/data):

#### Pure DVC Pipeline (CPU-bound)

```yaml
# For standard download/process/analyze pipelines
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: data-pipeline
spec:
  entrypoint: main
  templates:
    - name: single-pipeline
      script:
        image: opencloudhuborg/data-registry-pipelines:latest
        source: |
          dvc repro pipelines/${PIPELINE}/dvc.yaml
          dvc push
          # Auto-version and tag...
```

#### Ray Data Pipeline (Distributed)

```yaml
# For compute-heavy pipelines like embeddings
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: embeddings-pipeline
spec:
  templates:
    - name: create-rayjob
      # Creates a RayJob resource for distributed processing
      # Scales across Ray cluster workers
```

### Scaling Considerations

| Pipeline Type            | Execution Method        | When to Use                   |
| ------------------------ | ----------------------- | ----------------------------- |
| Simple download/process  | DVC in single container | Small datasets, I/O bound     |
| Large dataset processing | Ray Data on cluster     | CPU-intensive, parallelizable |
| Embedding generation     | Ray + GPU workers       | GPU-accelerated inference     |

**Future improvements:**

- Separate container images per pipeline for faster cold starts
- Pipeline-specific resource limits
- Caching of intermediate artifacts

______________________________________________________________________

<h2 id="project-structure">📁 Project Structure</h2>

```
data-registry/
├── data/
│   ├── fashion-mnist/          # Image classification dataset
│   │   ├── raw/                # Downloaded files (DVC-tracked)
│   │   ├── processed/          # Parquet files (DVC-tracked)
│   │   └── metadata.json       # Dataset stats (git-tracked)
│   ├── emotion/                # Text emotion dataset
│   ├── wine-quality/           # Tabular regression dataset
│   ├── radiology-mini/         # VLM training dataset
│   │   ├── raw/
│   │   │   ├── images/         # X-ray images
│   │   │   └── captions.json   # Image descriptions
│   │   └── processed/
│   │       ├── train/
│   │       │   ├── images/
│   │       │   └── annotations.json
│   │       └── test/
│   ├── opencloudhub-readmes/   # README markdown files
│   └── opencloudhub-readmes-embeddings/  # Embeddings metadata
│
├── pipelines/
│   ├── fashion-mnist/
│   │   ├── dvc.yaml            # Pipeline stages definition
│   │   ├── params.yaml         # Pipeline parameters
│   │   └── scripts/
│   │       ├── download.py     # Stage 1: Download
│   │       ├── process.py      # Stage 2: Transform
│   │       └── analyze.py      # Stage 3: Compute stats
│   ├── roco-radiology/         # Radiology VLM dataset pipeline
│   ├── opencloudhub-readmes-download/
│   └── opencloudhub-readmes-embeddings/  # Ray Data pipeline
│       ├── dvc.yaml
│       ├── params.py           # Python-based config
│       └── scripts/
│           └── process.py      # Ray Data distributed processing
│
├── .github/workflows/
│   ├── run-data-pipelines.yaml      # Trigger DVC pipelines
│   └── run-embeddings-pipeline.yaml # Trigger Ray embeddings
│
├── .dvc/
│   └── config                  # DVC remote configuration
│
├── .env.docker                 # Local Docker Compose env
└── .env.minikube              # Minikube/K8s env
```

______________________________________________________________________

<h2 id="storage-backends">💾 Storage Backends</h2>

### Local Docker Compose (Development)

Use when developing locally with Docker Compose infrastructure:

```bash
# Source environment
set -a && source .env.docker && set +a

# DVC config points to localhost MinIO
dvc remote default local
```

**Configuration in `.dvc/config`:**

```ini
['remote "local"']
    url = s3://dvcstore
    endpointurl = http://localhost:9000
```

### MinIO on Kubernetes (Production)

For minikube or production cluster:

```bash
set -a && source .env.minikube && set +a
dvc remote default minio
```

**Configuration:**

```ini
['remote "minio"']
    url = s3://dvcstore
    endpointurl = https://minio-api.internal.opencloudhub.org
    ssl_verify = false
```

### Switching Remotes

```bash
dvc remote list           # Show available remotes
dvc remote default local  # Switch to local
dvc remote default minio  # Switch to production
dvc push -r minio         # Push to specific remote
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
- [Argo Workflows](https://argoproj.github.io/workflows/) - Kubernetes workflow orchestration
- [MinIO](https://min.io/) - S3-compatible object storage
- [MLflow](https://mlflow.org/) - ML lifecycle management

<p align="right">(<a href="#readme-top">back to top</a>)</p>
