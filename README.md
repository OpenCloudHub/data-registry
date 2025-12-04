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
    Versioned datasets for reproducible ML training using <a href="https://dvc.org/"><strong>DVC</strong></a>.<br />
    <a href="https://github.com/opencloudhub"><strong>Explore OpenCloudHub »</strong></a>
  </p>
</div>

---

<details>
  <summary>📑 Table of Contents</summary>
  <ol>
    <li><a href="#about">About</a></li>
    <li><a href="#thesis-context">Thesis Context</a></li>
    <li><a href="#features">Features</a></li>
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#configuration">Configuration</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

---

<h2 id="about">🎯 About</h2>

This repository manages **dataset preparation, versioning, and distribution** for ML training pipelines. It demonstrates how to build reproducible data pipelines using [DVC](https://dvc.org/) (Data Version Control) as part of a complete MLOps platform.

### Why DVC?

> *"What exact samples were in the training data for model v2.3 that we deployed two weeks ago?"*

DVC solves a fundamental problem in ML: **tracking which exact data was used to train a model**.

**The Problem:**

- Raw data changes over time (new samples, corrections, augmentations)
- Training results become unreproducible
- No way to rollback to a known-good dataset state
- Large files don't belong in Git

**The Solution:** DVC creates **git-like versioning for data**:

```bash
# Data versions are tied to git tags
git tag fashion-mnist-v1.0.0   # Points to specific dvc.lock
git tag fashion-mnist-v1.1.0   # New data version

# Training code references exact version
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    --rev fashion-mnist-v1.0.0
```

### Available Datasets

| Dataset | Description | Format | Use Case |
|---------|-------------|--------|----------|
| `fashion-mnist` | Fashion product images | Parquet (images + labels) | Image classification |
| `emotion` | Text emotion dataset | Parquet (text + labels) | Text classification |
| `wine-quality` | Wine quality ratings | CSV | Tabular regression |
| `roco-radiology` | Medical X-ray images with captions | Images + JSON annotations | Vision-Language Models (VLM) |
| `opencloudhub-readmes` | Repository README files | Markdown files | RAG / Embeddings |
| `opencloudhub-readmes-embeddings` | Vectorized READMEs | pgvector database | Semantic search |

---

<h2 id="thesis-context">📚 Thesis Context</h2>

This repository is part of the **OpenCloudHub MLOps Platform** thesis project, demonstrating enterprise-grade ML infrastructure patterns.

### Role in Platform Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MLOPS PLATFORM LAYERS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 1: INFRASTRUCTURE (infra-modules, infra-live)                        │
│    └─ Kubernetes, MinIO, PostgreSQL, MLflow, Ray, Argo                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 2: DATA MANAGEMENT  ◄── THIS REPOSITORY                             │
│    └─ DVC pipelines, versioned datasets, embeddings generation             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 3: ML WORKLOADS (ai-ml-sklearn, ai-dl-bert, ai-radiology-qwen)       │
│    └─ Training jobs consuming versioned data from Layer 2                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Requirements Demonstrated

| Requirement | Implementation | Files |
|-------------|----------------|-------|
| **Data Versioning** | DVC with git tags for immutable dataset versions | `dvc.yaml`, `dvc.lock` |
| **Data Lineage** | Metadata tracking source version, model, parameters | `metadata.json` files |
| **Reproducibility** | Version-pinned data access via `dvc get --rev` | Pipeline scripts |
| **Distributed Processing** | Ray Data for scalable embeddings generation | `process.py` |
| **MLflow Integration** | Prompt Registry for VLM instruction management | `roco-radiology/process.py` |
| **GitOps Automation** | GitHub Actions → Argo Workflows for production runs | `.github/workflows/` |

### Key Implementation Patterns

1. **DVC + Git Tags Pattern**: Data versions tied to git tags enable training code to reference exact dataset snapshots
2. **Metadata as Metrics**: Statistics computed at pipeline completion, tracked by DVC for monitoring
3. **Environment-based Configuration**: Secrets via env vars, switching between local/cluster via `.env.*` files
4. **Ray Data for Scale**: Distributed processing with batched embedding generation and database writes
5. **MLflow Prompt Registry**: Version-controlled prompts for VLM training data preparation

### Data Flow Through the Platform

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA REGISTRY                                     │
│  fashion-mnist-v1.0.0 → MinIO (s3://dvcstore/files/md5/...)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRAINING JOB                                       │
│  Input: data_version=fashion-mnist-v1.0.0                                   │
│  Output: model artifact + MLflow run                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MLFLOW TRACKING                                     │
│  Params:                                                                    │
│    - data_version: fashion-mnist-v1.0.0                                     │
│    - data_pixel_mean: 0.2860                                                │
│    - data_pixel_std: 0.3530                                                 │
│  → Full reproducibility: same data + same code = same model                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

<h2 id="features">✨ Features</h2>

- **📊 Automated Data Pipelines**: Download → Process → Analyze workflow with DVC
- **🔄 Version Control**: Git tags + DVC for immutable dataset versions
- **📈 Automatic Metrics**: Statistics computed and tracked per dataset
- **🔀 Flexible Storage**: Local Docker Compose or MinIO cluster backends
- **🚀 Easy Integration**: Seamless use in training repos via `dvc get` or Python API
- **☸️ Production Patterns**: GitHub Actions + Argo Workflows for cluster execution
- **⚡ Ray Data Integration**: Distributed processing for large datasets
- **🧠 Embeddings Pipeline**: RAG-ready vector generation with pgvector storage
- **🧪 Development Environment**: VS Code DevContainer with all tools pre-configured

---

<h2 id="architecture">🏗️ Architecture</h2>

### Pipeline Stages

Each dataset follows a three-stage pipeline pattern:

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   DOWNLOAD   │ ──► │   PROCESS    │ ──► │   ANALYZE    │
│              │     │              │     │              │
│ Fetch raw    │     │ Transform to │     │ Compute      │
│ data from    │     │ ML-ready     │     │ statistics   │
│ source       │     │ format       │     │ & metadata   │
└──────────────┘     └──────────────┘     └──────────────┘
      │                    │                    │
      ▼                    ▼                    ▼
   data/raw/         data/processed/      metadata.json
   (DVC-tracked)     (DVC-tracked)        (git-tracked)
```

### Production Execution

In production, pipelines run on Kubernetes via GitHub Actions and Argo Workflows:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION OPTIONS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. LOCAL (Development)                                                     │
│     └─ dvc repro pipelines/fashion-mnist/dvc.yaml                           │
│                                                                             │
│  2. GITHUB ACTIONS → ARGO WORKFLOWS (Production)                            │
│     └─ Trigger via workflow_dispatch or schedule                            │
│     └─ Submits Argo Workflow to Kubernetes cluster                          │
│     └─ Auto-tags with semantic versioning                                   │
│                                                                             │
│  3. RAY DATA (Distributed Processing)                                       │
│     └─ For compute-heavy pipelines (embeddings, large datasets)             │
│     └─ Scales across Ray cluster workers                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Embeddings Pipeline (RAG)

The embeddings pipeline demonstrates a more complex architecture for RAG systems:

```text
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  DVC (READMEs) │ ──► │   Ray Data     │ ──► │   pgvector     │
│                │     │                │     │                │
│ Version-tagged │     │ Chunk + Embed  │     │ LangChain-     │
│ source data    │     │ (distributed)  │     │ compatible     │
└────────────────┘     └────────────────┘     └────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
  Git tag:              sentence-transformers    Vector search
  readmes-v1.0.0        all-MiniLM-L6-v2        for RAG apps
```

---

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

2. **Open in DevContainer** (Recommended)

   VS Code: `Ctrl+Shift+P` → `Dev Containers: Rebuild and Reopen in Container`

3. **Configure environment**

   Choose your backend (see [Configuration](#configuration) for details):

   ```bash
   # For local Docker Compose setup
   set -a && source .env.docker && set +a

   # For Minikube/Kubernetes setup
   set -a && source .env.minikube && set +a
   ```

### Running a Pipeline

```bash

# Run all stages of FashionMNIST pipeline
dvc repro pipelines/fashion-mnist/dvc.yaml

# Or run specific stage
dvc repro download
dvc repro process
dvc repro analyze

# Check results
cat ../../data/fashion-mnist/metadata.json
```

### Bootstrap All Datasets

For quick setup with all datasets at v1.0.0:

```bash
./scripts/bootstrap-data-examples.sh

# With forced re-run (ignore cache)
./scripts/bootstrap-data-examples.sh --force

# Include embeddings pipeline (requires pgvector)
./scripts/bootstrap-data-examples.sh --with-embeddings
```

### Using Datasets in Training Code

**Option 1: DVC CLI**

```bash
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    -o ./data/fashion-mnist \
    --rev fashion-mnist-v1.0.0
```

**Option 2: Python API (Recommended)**

```python
import dvc.api
import json

REPO = "https://github.com/OpenCloudHub/data-registry"
VERSION = "fashion-mnist-v1.0.0"

# Get S3 URL for direct loading with Ray Data
train_url = dvc.api.get_url(
    "data/fashion-mnist/processed/train/train.parquet",
    repo=REPO,
    rev=VERSION
)

# Load metadata for normalization parameters
metadata = json.loads(
    dvc.api.read("data/fashion-mnist/metadata.json", repo=REPO, rev=VERSION)
)

# Log to MLflow for reproducibility
import mlflow
mlflow.log_params({
    "data_version": VERSION,
    "data_pixel_mean": metadata["metrics"]["train"]["pixel_mean"],
})
```

---

<h2 id="configuration">⚙️ Configuration</h2>

### Storage Backends

The repository supports two storage backends, configured via environment files and DVC remotes.

#### Local Docker Compose (Development)

For local development with Docker Compose infrastructure:

```bash
# 1. Source environment variables
set -a && source .env.docker && set +a

# 2. Set DVC remote to docker
dvc remote default docker

# 3. Run pipelines
dvc repro pipelines/fashion-mnist/dvc.yaml
dvc push
```

**Configuration:**

- MinIO endpoint: `http://localhost:9000`
- pgvector: `localhost:5432`
- MLflow: `http://localhost:5000`

#### Minikube/Kubernetes (Production-like)

For testing with Kubernetes infrastructure:

```bash
# 1. Source environment variables
set -a && source .env.minikube && set +a

# 2. Set DVC remote to minikube (default)
dvc remote default minikube

# 3. Port-forward services if needed
kubectl port-forward -n storage svc/demo-app-db-pooler 5432:5432

# 4. Run pipelines
dvc repro pipelines/fashion-mnist/dvc.yaml
dvc push
```

**Configuration:**

- MinIO endpoint: `https://minio-api.internal.opencloudhub.org`
- pgvector: port-forwarded to `localhost:5432`
- MLflow: `https://mlflow.internal.opencloudhub.org`

### DVC Remote Configuration

```bash
# List available remotes
dvc remote list

# Switch default remote
dvc remote default docker    # Local development
dvc remote default minikube  # Kubernetes

# Push to specific remote
dvc push -r minikube
```

**Remote definitions in `.dvc/config`:**

```ini
[core]
    remote = minikube

['remote "minikube"']
    url = s3://dvcstore
    endpointurl = https://minio-api.internal.opencloudhub.org

['remote "docker"']
    url = s3://dvcstore
    endpointurl = http://localhost:9000
```

### Embeddings Pipeline Configuration

The embeddings pipeline requires additional environment variables for database access:

```bash
# Required for embeddings pipeline
export PGVECTOR_HOST=localhost
export PGVECTOR_PORT=5432
export PGVECTOR_DATABASE=vectors
export PGVECTOR_USER=admin
export PGVECTOR_PASSWORD=admin
export PGVECTOR_TABLE_NAME=readme_embeddings
```

Parameters are defined in `pipelines/opencloudhub-readmes-embeddings/params.py`:

```python
# Data source (DVC version tag)
DVC_DATA_VERSION = "opencloudhub-readmes-v1.0.0"
DVC_DATA_PATH = "data/opencloudhub-readmes/raw"

# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 1500
EMBEDDING_CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 4
```

---

<h2 id="project-structure">📁 Project Structure</h2>

```text
data-registry/
├── data/                           # Dataset storage (DVC-tracked)
│   ├── fashion-mnist/
│   │   ├── raw/                    # Downloaded IDX files
│   │   ├── processed/              # Parquet files (train/val)
│   │   └── metadata.json           # Statistics (git-tracked)
│   ├── emotion/                    # Text classification dataset
│   ├── wine-quality/               # Tabular regression dataset
│   ├── roco-radiology/             # VLM training dataset
│   │   ├── raw/images/             # Original X-ray images
│   │   └── processed/              # Qwen conversation format
│   ├── opencloudhub-readmes/       # README markdown files
│   └── opencloudhub-readmes-embeddings/
│       └── metadata.json           # Embeddings pipeline stats
│
├── pipelines/                      # DVC pipeline definitions
│   ├── fashion-mnist/
│   │   ├── dvc.yaml                # Pipeline stages
│   │   ├── params.yaml             # Configuration
│   │   └── scripts/
│   │       ├── download.py         # Stage 1: Download
│   │       ├── process.py          # Stage 2: Transform
│   │       └── analyze.py          # Stage 3: Compute stats
│   ├── emotion/                    # Same structure
│   ├── wine-quality/               # Same structure
│   ├── roco-radiology/             # VLM dataset pipeline
│   ├── opencloudhub-readmes-download/
│   └── opencloudhub-readmes-embeddings/
│       ├── dvc.yaml
│       ├── params.py               # Python config for DVC
│       ├── run_pipeline.py         # Production wrapper
│       └── scripts/
│           ├── process.py          # Ray Data pipeline
│           └── analyze.py          # Metadata generation
│
├── scripts/
│   └── bootstrap-data-examples.sh  # Initialize all datasets
│
├── .github/workflows/
│   ├── run-data-pipelines.yaml     # Trigger DVC pipelines via Argo
│   └── run-embeddings-pipeline.yaml # Trigger Ray embeddings via Argo
│
├── .dvc/
│   ├── config                      # DVC remote configuration (git-tracked)
│   └── config.local                # Local overrides (git-ignored)
│
├── .env.docker                     # Local Docker Compose environment
├── .env.minikube                   # Minikube/K8s environment
├── Dockerfile                      # Multi-stage: dev + prod (Ray)
└── pyproject.toml                  # Python dependencies
```

---

<h2 id="contributing">👥 Contributing</h2>

Contributions are welcome! This project follows OpenCloudHub's contribution standards.

Please see our [Contributing Guidelines](https://github.com/opencloudhub/.github/blob/main/.github/CONTRIBUTING.md) and [Code of Conduct](https://github.com/opencloudhub/.github/blob/main/.github/CODE_OF_CONDUCT.md) for more details.

---

<h2 id="license">📄 License</h2>

Distributed under the Apache 2.0 License. See [LICENSE](LICENSE) for more information.

---

<h2 id="contact">📬 Contact</h2>

- **Organization:** [OpenCloudHub](https://github.com/OpenCloudHub)
- **Project:** [data-registry](https://github.com/opencloudhub/data-registry)
- **Documentation:** [OpenCloudHub Docs](https://opencloudhub.github.io/docs)

---

<h2 id="acknowledgements">🙏 Acknowledgements</h2>

- [DVC](https://dvc.org/) - Data version control
- [Ray Data](https://docs.ray.io/en/latest/data/data.html) - Distributed data loading
- [Argo Workflows](https://argoproj.github.io/workflows/) - Kubernetes workflow orchestration
- [MinIO](https://min.io/) - S3-compatible object storage
- [MLflow](https://mlflow.org/) - ML lifecycle management
- [sentence-transformers](https://www.sbert.net/) - Embedding generation
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<div align="center">
  <h3>🌟 Follow the Journey</h3>
  <p><em>Building in public • Learning together • Sharing knowledge</em></p>

  <div>
    <a href="https://opencloudhub.github.io/docs">
      <img src="https://img.shields.io/badge/Read%20the%20Docs-2596BE?style=for-the-badge&logo=read-the-docs&logoColor=white" alt="Documentation">
    </a>
    <a href="https://github.com/orgs/opencloudhub/discussions">
      <img src="https://img.shields.io/badge/Join%20Discussion-181717?style=for-the-badge&logo=github&logoColor=white" alt="Discussions">
    </a>
    <a href="https://github.com/orgs/opencloudhub/projects/4">
      <img src="https://img.shields.io/badge/View%20Roadmap-0052CC?style=for-the-badge&logo=jira&logoColor=white" alt="Roadmap">
    </a>
  </div>
</div>
