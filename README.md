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

<h1 align="center">Data Registry — Versioned Datasets for ML</h1>

<p align="center">
    Centralized data versioning with DVC, demonstrating reproducible ML data pipelines and metadata-driven training.<br />
    <a href="https://github.com/opencloudhub"><strong>Explore OpenCloudHub »</strong></a>
  </p>
</div>

______________________________________________________________________

<details>
  <summary>📑 Table of Contents</summary>
  <ol>
    <li><a href="#about">About</a></li>
    <li><a href="#thesis-context">Thesis Context</a></li>
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="#pipelines">Pipelines</a></li>
    <li><a href="#code-structure">Code Structure</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#infrastructure">Infrastructure Options</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#configuration">Configuration</a></li>
    <li><a href="#design-decisions">Design Decisions</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>

______________________________________________________________________

<h2 id="about">🎯 About</h2>

This repository manages **dataset preparation, versioning, and distribution** for ML training pipelines. It demonstrates how to build reproducible data pipelines using [DVC](https://dvc.org/) (Data Version Control) as part of a complete MLOps platform.

### The Problem DVC Solves

> *"What exact samples were in the training data for model v2.3 that we deployed two weeks ago?"*

In ML, **data is as important as code** — but traditional version control doesn't handle large files or binary data well:

- Raw data changes over time (new samples, corrections, augmentations)
- Training results become unreproducible without knowing exact data state
- No way to rollback to a known-good dataset state
- Large files (images, embeddings) don't belong in Git

**DVC creates git-like versioning for data:**

```bash
# Data versions are tied to git tags
git tag fashion-mnist-v1.0.0   # Points to specific dvc.lock
git tag fashion-mnist-v1.1.0   # New data version after processing changes

# Training code references exact version
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    --rev fashion-mnist-v1.0.0
```

### Available Datasets

Each dataset is prepared for a specific ML workload in the platform:

| Dataset                           | Format                | Training Repo                                                                    | Use Case                         |
| --------------------------------- | --------------------- | -------------------------------------------------------------------------------- | -------------------------------- |
| `wine-quality`                    | CSV → Parquet         | [ai-ml-sklearn](https://github.com/opencloudhub/ai-ml-sklearn)                   | Baseline tabular regression      |
| `fashion-mnist`                   | IDX → Parquet         | [ai-dl-lightning](https://github.com/opencloudhub/ai-dl-lightning)               | Distributed image classification |
| `emotion`                         | HuggingFace → Parquet | [ai-dl-bert](https://github.com/opencloudhub/ai-dl-bert)                         | Text classification with HPO     |
| `roco-radiology`                  | Images + JSON         | [ai-dl-qwen](https://github.com/opencloudhub/ai-dl-qwen)                         | VLM fine-tuning                  |
| `opencloudhub-readmes`            | GitHub → Markdown     | *(intermediate)*                                                                 | Source data for embeddings       |
| `opencloudhub-readmes-embeddings` | Markdown → pgvector   | [demo-app-genai-backend](https://github.com/opencloudhub/demo-app-genai-backend) | RAG semantic search              |

Note: The embeddings pipeline depends on the readmes-download pipeline, creating a two-stage lineage chain.

______________________________________________________________________

<h2 id="thesis-context">📚 Thesis Context</h2>

This repository is part of a Master's thesis: **"A Scalable MLOps System for Multimodal Educational Analysis"** at Goethe University Frankfurt / DIPF Leibniz Institute.

### Role in the Platform

The Data Registry sits at Layer 2 of the platform architecture — **between infrastructure and ML workloads**. All training jobs consume versioned data from this central registry, ensuring reproducibility across the entire ML lifecycle.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 1: INFRASTRUCTURE                                                    │
│    └─ Kubernetes, MinIO, PostgreSQL, MLflow, Ray, Argo                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 2: DATA MANAGEMENT  ◄── THIS REPOSITORY                              │
│    └─ DVC pipelines, versioned datasets, embeddings generation              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Layer 3: ML WORKLOADS                                                      │
│    └─ ai-ml-sklearn, ai-dl-lightning, ai-dl-bert, ai-dl-qwen                │
│    └─ All consume data via: dvc.api.get_url(rev="dataset-v1.0.0")           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Requirements Addressed

| Req ID   | Requirement          | Implementation                                             |
| -------- | -------------------- | ---------------------------------------------------------- |
| **FR2**  | Data Versioning      | DVC with git tags for immutable dataset snapshots          |
| **FR12** | RAG Pipeline Support | Embeddings pipeline with Ray Data + pgvector               |
| **FR13** | Prompt Versioning    | ROCO pipeline fetches prompts from MLflow Prompt Registry  |
| **NFR1** | End-to-End Lineage   | metadata.json tracks source, processing params, statistics |
| **NFR2** | Reproducibility      | Git tag → dvc.lock → exact data snapshot                   |
| **C1**   | Open-Source Only     | DVC, Ray Data, sentence-transformers — permissive licenses |
| **C2**   | Self-Hostable        | MinIO as S3-compatible storage backend                     |

### Key Patterns Demonstrated

| Pattern                      | Implementation                               | Why It Matters                                    |
| ---------------------------- | -------------------------------------------- | ------------------------------------------------- |
| **Git Tags = Data Versions** | `fashion-mnist-v1.0.0` → specific `dvc.lock` | Immutable snapshots for reproducibility           |
| **Metadata as Contract**     | `metadata.json` with normalization params    | Training and serving use same preprocessing       |
| **Three-Stage Pipelines**    | download → process → analyze                 | Separation of concerns, caching, reusability      |
| **Distributed Processing**   | Ray Data for embeddings pipeline             | Scale-out for compute-intensive pipelines         |
| **Prompt Lineage**           | ROCO fetches prompt from MLflow Registry     | Tracks which prompt was embedded in training data |

### Integration with ML Workloads

```mermaid
flowchart LR
    subgraph registry["Data Registry"]
        WINE[(wine-quality)]
        FMNIST[(fashion-mnist)]
        EMOTION[(emotion)]
        ROCO[(roco-radiology)]
        READMES[(opencloudhub-readmes)]
        EMBED[(readmes-embeddings)]
    end

    subgraph training["ML Workloads"]
        SKLEARN[ai-ml-sklearn]
        LIGHTNING[ai-dl-lightning]
        BERT[ai-dl-bert]
        QWEN[ai-dl-qwen]
        RAG[demo-app-genai-backend]
    end

    WINE -->|"wine-v1.0.0"| SKLEARN
    FMNIST -->|"fashion-mnist-v1.0.0"| LIGHTNING
    EMOTION -->|"emotion-v1.0.0"| BERT
    ROCO -->|"roco-v1.0.0"| QWEN
    READMES -->|"depends on"| EMBED
    EMBED -->|"pgvector"| RAG
```

______________________________________________________________________

<h2 id="architecture">🏗️ Architecture</h2>

### DVC Version Control Model

```mermaid
flowchart TB
    subgraph git["Git Repository"]
        DVC_YAML["dvc.yaml
        (pipeline definition)"]
        DVC_LOCK["dvc.lock
        (data fingerprints)"]
        METADATA["metadata.json
        (statistics, params)"]
        GIT_TAG["git tag: fashion-mnist-v1.0.0"]
    end

    subgraph storage["MinIO (S3-Compatible)"]
        RAW["s3://dvcstore/files/md5/ab/...
        (raw data)"]
        PROCESSED["s3://dvcstore/files/md5/cd/...
        (processed data)"]
    end

    DVC_LOCK -->|"references"| RAW
    DVC_LOCK -->|"references"| PROCESSED
    GIT_TAG -->|"points to"| DVC_LOCK

    subgraph training["Training Job"]
        FETCH["dvc.api.get_url(rev='fashion-mnist-v1.0.0')"]
        LOAD["Load exact data snapshot"]
    end

    GIT_TAG -->|"resolves to"| FETCH
    FETCH -->|"downloads"| LOAD
    RAW -.->|"content"| LOAD
    PROCESSED -.->|"content"| LOAD
```

**Key insight:** `dvc.lock` contains MD5 hashes of all data files. When you checkout a git tag, you get the exact `dvc.lock` from that point in time — which points to the exact data files in MinIO.

### Three-Stage Pipeline Pattern

Every dataset follows the same pipeline structure:

```mermaid
flowchart LR
    subgraph download["Stage 1: DOWNLOAD"]
        D_IN[External Source]
        D_OUT["data/raw/
        (DVC-tracked)"]
    end

    subgraph process["Stage 2: PROCESS"]
        P_IN[Raw Data]
        P_OUT["data/processed/
        (DVC-tracked)"]
    end

    subgraph analyze["Stage 3: ANALYZE"]
        A_IN[Processed Data]
        A_OUT["metadata.json
        (Git-tracked)"]
    end

    D_IN --> D_OUT
    D_OUT --> P_IN --> P_OUT
    P_OUT --> A_IN --> A_OUT

    style D_OUT fill:#e1f5fe
    style P_OUT fill:#e1f5fe
    style A_OUT fill:#fff3e0
```

**Why this structure:**

- **Download** — Fetches from external source, cached to avoid repeated downloads
- **Process** — Transforms to ML-ready format, can be re-run if processing logic changes
- **Analyze** — Computes statistics (mean, std, class distribution) needed for training

### Metadata Flow to Training

```mermaid
sequenceDiagram
    participant DVC as Data Registry
    participant Train as Training Job
    participant MLflow as MLflow

    Train->>DVC: dvc.api.read("metadata.json", rev="fashion-mnist-v1.0.0")
    DVC-->>Train: {"pixel_mean": 0.286, "pixel_std": 0.353, ...}

    Train->>Train: Apply normalization with metadata params
    Train->>MLflow: log_params({"data_version": "fashion-mnist-v1.0.0", "pixel_mean": 0.286})

    Note over Train,MLflow: Model now linked to exact data snapshot + preprocessing params
```

This pattern ensures **training-serving consistency**: the serving endpoint uses the same normalization parameters that were computed during data processing.

### Production Execution via Argo Workflows

```mermaid
flowchart TB
    subgraph github["GitHub"]
        DISPATCH[Workflow Dispatch]
        ACTION[GitHub Action]
    end

    subgraph cluster["Kubernetes Cluster"]
        ARGO[Argo Workflows]

        subgraph job["DVC Pipeline Job"]
            CLONE[Clone Repo]
            REPRO["dvc repro"]
            PUSH["dvc push"]
            TAG["git tag + push"]
        end
    end

    subgraph storage["MinIO"]
        DATA[(Versioned Data)]
    end

    DISPATCH -->|"inputs: dataset, version"| ACTION
    ACTION -->|"submit workflow"| ARGO
    ARGO --> CLONE --> REPRO --> PUSH --> TAG
    REPRO -->|"outputs"| DATA
    PUSH -->|"uploads"| DATA
```

______________________________________________________________________

<h2 id="pipelines">📊 Pipelines</h2>

### Pipeline Overview

Each pipeline lives in `pipelines/<dataset>/` and consists of:

- `dvc.yaml` — Pipeline stage definitions
- `params.yaml` — Configuration parameters
- `scripts/` — Python scripts for each stage

### wine-quality (Baseline Tabular)

**Purpose:** Demonstrates simplest DVC pipeline with tabular data.

```yaml
# pipelines/wine-quality/dvc.yaml
stages:
  download:
    cmd: python scripts/download.py
    params: [download]
    outs: [../../data/wine-quality/raw]

  process:
    cmd: python scripts/process.py
    deps: [../../data/wine-quality/raw]
    params: [process]
    outs: [../../data/wine-quality/processed]

  analyze:
    cmd: python scripts/analyze.py
    deps: [../../data/wine-quality/processed]
    metrics: [../../data/wine-quality/metadata.json]
```

**Metadata output:** Feature statistics (mean, std, min, max) for normalization.

### fashion-mnist (Distributed Training)

**Purpose:** Image data with normalization parameters critical for training-serving consistency.

**Key metadata:**

```json
{
  "metrics": {
    "train": {
      "pixel_mean": 0.2860,
      "pixel_std": 0.3530,
      "num_samples": 60000
    }
  }
}
```

The training job fetches these values and:

1. Uses them for normalization during training
1. Logs them to MLflow as parameters
1. The serving endpoint loads them from DVC via the MLflow run's `dvc_data_version` tag

### emotion (HPO with Text)

**Purpose:** Text classification dataset for hyperparameter optimization demo.

**Key metadata:**

```json
{
  "label_map": {
    "0": "sadness",
    "1": "joy",
    "2": "love",
    "3": "anger",
    "4": "fear",
    "5": "surprise"
  }
}
```

The label mapping is logged as an MLflow artifact, ensuring the serving endpoint knows how to map model outputs to emotion names.

### roco-radiology (VLM with Prompt Versioning)

**Purpose:** Vision-Language Model fine-tuning with prompt lineage tracking.

**Key innovation:** The process stage fetches the prompt template from MLflow Prompt Registry:

```python
# pipelines/roco-radiology/scripts/process.py (conceptual)
prompt_info = mlflow.get_prompt(name="radiology-caption", version="1")

# Each processed sample includes the prompt
processed_sample = {
    "image": image_path,
    "conversations": [
        {"role": "user", "content": prompt_info.template + " {image}"},
        {"role": "assistant", "content": caption},
    ],
}
```

**Metadata tracks prompt lineage:**

```json
{
  "prompt": {
    "prompt_name": "radiology-caption",
    "prompt_version": 1,
    "prompt_template": "Describe this radiology image in detail..."
  }
}
```

### opencloudhub-readmes-embeddings (RAG Pipeline)

**Purpose:** Demonstrates Ray Data for batch embedding generation with full lineage tracking.

**Pipeline Dependency Chain:**

This pipeline depends on another pipeline, creating a two-stage lineage:

```mermaid
flowchart LR
    subgraph stage1["Pipeline 1: readmes-download"]
        FETCH[Fetch READMEs from GitHub]
        RAW["data/opencloudhub-readmes/raw/
        (DVC-versioned)"]
    end

    subgraph stage2["Pipeline 2: readmes-embeddings"]
        DVC_GET["dvc.api.get_url
        (rev=opencloudhub-readmes-v1.0.0)"]
        RAYDATA[Ray Data Pipeline]
        PGVECTOR[(pgvector)]
    end

    FETCH --> RAW
    RAW -->|"git tag"| DVC_GET
    DVC_GET --> RAYDATA --> PGVECTOR
```

**Ray Data Processing Flow:**

```mermaid
flowchart LR
    subgraph raydata["Ray Data Pipeline (Batch Processing)"]
        READ["ray.data.read_text
        (streaming from S3)"]
        CHUNK["Chunker
        (Markdown-aware splitting)"]
        EMBED["Embedder
        (batched inference)"]
        WRITE["PGVectorWriter
        (batched inserts)"]
    end

    READ --> CHUNK --> EMBED --> WRITE
```

**Why Ray Data here:**

The embeddings pipeline uses Ray Data not for distributed cluster execution, but to demonstrate the **batch processing pattern** that Ray enables:

- **Batch inference** — The embedder processes chunks in batches (e.g., batch_size=8) rather than one-by-one, significantly improving throughput
- **Streaming** — Reads from S3/MinIO without materializing all files in memory
- **Same framework** — Shows that Ray (used for training) can also handle data processing, reducing tool sprawl

This pattern could scale to distributed execution if needed — the code structure supports it — but in this demo it runs single-node to keep resource requirements manageable.

**Full Lineage in Vector Database:**

Every chunk stored in pgvector includes complete workflow metadata:

```python
{
    # Content metadata
    "source_repo": "opencloudhub/ai-ml-sklearn",
    "source_file": "README.md",
    "chunk_index": 3,
    "section_h1": "Getting Started",
    "section_h2": "Installation",
    # Data lineage (which version of source READMEs)
    "dvc_data_version": "opencloudhub-readmes-v1.0.0",
    # Processing lineage (which code/workflow produced this)
    "embedding_model": "all-MiniLM-L6-v2",
    "docker_image": "sha-abc123",
    "argo_workflow_uid": "workflow-xyz",
}
```

**Why this matters for evaluation:**

When comparing RAG prompt performance, you need to know which embeddings were used. The workflow tags enable queries like:

```sql
-- Compare retrieval quality across embedding versions
SELECT * FROM readme_embeddings
WHERE dvc_data_version = 'opencloudhub-readmes-v1.0.0'
  AND argo_workflow_uid = 'workflow-xyz';
```

This allows A/B testing different embedding models or chunk strategies while maintaining complete traceability

```

______________________________________________________________________

<h2 id="code-structure">📂 Code Structure</h2>

### Project Layout

```

data-registry/
├── data/ # Dataset storage (DVC-tracked)
│ ├── wine-quality/
│ │ ├── raw/ # Downloaded CSV
│ │ ├── processed/ # Train/test Parquet
│ │ └── metadata.json # Statistics (Git-tracked)
│ ├── fashion-mnist/
│ │ ├── raw/ # IDX files
│ │ ├── processed/train/ # Parquet with images + labels
│ │ ├── processed/val/ # Validation split
│ │ └── metadata.json # pixel_mean, pixel_std
│ ├── emotion/
│ │ └── ... # Same structure
│ ├── roco-radiology/
│ │ ├── raw/images/ # X-ray images
│ │ ├── processed/train/ # Qwen conversation format
│ │ └── metadata.json # Includes prompt_version
│ └── opencloudhub-readmes-embeddings/
│ └── metadata.json # Embedding pipeline stats
│
├── pipelines/ # DVC pipeline definitions
│ ├── wine-quality/
│ │ ├── dvc.yaml # Pipeline stages
│ │ ├── params.yaml # Configuration
│ │ └── scripts/
│ │ ├── download.py # Fetch from UCI ML Repo
│ │ ├── process.py # Train/test split, Parquet
│ │ └── analyze.py # Compute feature statistics
│ ├── fashion-mnist/ # Same structure
│ ├── emotion/ # Same structure
│ ├── roco-radiology/ # Same structure + prompt fetch
│ ├── opencloudhub-readmes-download/ # Fetch README files
│ └── opencloudhub-readmes-embeddings/
│ ├── dvc.yaml
│ ├── params.py # Python config (chunk size, model)
│ └── scripts/
│ ├── process.py # Ray Data pipeline
│ └── analyze.py # Metadata generation
│
├── scripts/
│ ├── bootstrap-data-examples.sh # Initialize all datasets for local dev
│ └── reset-for-demo.sh # Reset DVC state for fresh demo
│
├── .github/workflows/
│ ├── run-data-pipelines.yaml # Trigger DVC pipelines via Argo
│ └── run-embeddings-pipeline.yaml # Trigger Ray embeddings via Argo
│
├── .dvc/
│ └── config # DVC remote configuration
├── .env.docker # Local environment
├── .env.minikube # Cluster environment
└── Dockerfile # Multi-stage: dev + prod

````

### DVC Pipeline Definition Pattern

```yaml
# pipelines/fashion-mnist/dvc.yaml
stages:
  download:
    cmd: python scripts/download.py
    deps:
      - scripts/download.py           # Re-run if script changes
    params:
      - download.base_url             # Re-run if config changes
    outs:
      - ../../data/fashion-mnist/raw  # DVC tracks these files

  process:
    cmd: python scripts/process.py
    deps:
      - scripts/process.py
      - ../../data/fashion-mnist/raw  # Depends on download output
    params:
      - process                       # All process.* params
    outs:
      - ../../data/fashion-mnist/processed/train
      - ../../data/fashion-mnist/processed/val

  analyze:
    cmd: python scripts/analyze.py
    deps:
      - scripts/analyze.py
      - ../../data/fashion-mnist/processed/train
      - ../../data/fashion-mnist/processed/val
    metrics:
      - ../../data/fashion-mnist/metadata.json:
          cache: false                # Keep in Git, not DVC
````

**Key DVC concepts:**

- **deps** — Files that trigger re-run when changed
- **params** — YAML parameters that trigger re-run when changed
- **outs** — Output files tracked by DVC (stored in MinIO)
- **metrics** — Output files tracked by Git (for easy viewing)

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

1. **Choose infrastructure backend** (see next section)

______________________________________________________________________

<h2 id="infrastructure">🛠️ Infrastructure Options</h2>

### Option 1: Local Compose Stack

For development with local MinIO storage.

```bash
# Start MinIO + MLflow
git clone https://github.com/OpenCloudHub/local-compose-stack.git
cd local-compose-stack && docker compose up -d

# Configure DVC
cd ../data-registry
set -a && source .env.docker && set +a
dvc remote default docker
```

**Available Services:**

| Service       | URL                   |
| ------------- | --------------------- |
| MinIO Console | http://localhost:9001 |
| MLflow UI     | http://localhost:5000 |

### Option 2: Minikube with Platform Services

Use MinIO deployed on Minikube.

```bash
set -a && source .env.minikube && set +a
dvc remote default minikube
```

### Option 3: Production via Argo Workflows

Pipelines run on Kubernetes, triggered by GitHub Actions.

**Trigger pipeline:** [Actions → Run Data Pipelines](https://github.com/OpenCloudHub/data-registry/actions/workflows/run-data-pipelines.yaml)

______________________________________________________________________

<h2 id="usage">📖 Usage</h2>

### Running Pipelines Locally

```bash
# Run complete pipeline
dvc repro pipelines/fashion-mnist/dvc.yaml

# Run specific stage
cd pipelines/fashion-mnist
dvc repro analyze

# Push data to remote storage
dvc push
```

### Creating a Data Version

```bash
# After running pipeline and pushing data
git add dvc.lock data/fashion-mnist/metadata.json
git commit -m "Update fashion-mnist dataset"
git tag fashion-mnist-v1.0.0
git push origin fashion-mnist-v1.0.0
```

### Using Data in Training Code

**Python API (Recommended):**

```python
import dvc.api
import json

REPO = "https://github.com/OpenCloudHub/data-registry"
VERSION = "fashion-mnist-v1.0.0"

# Get S3 URL for Ray Data streaming
train_url = dvc.api.get_url(
    "data/fashion-mnist/processed/train/train.parquet", repo=REPO, rev=VERSION
)

# Load metadata for normalization
metadata = json.loads(
    dvc.api.read("data/fashion-mnist/metadata.json", repo=REPO, rev=VERSION)
)

# Use in training
pixel_mean = metadata["metrics"]["train"]["pixel_mean"]
pixel_std = metadata["metrics"]["train"]["pixel_std"]

# Log to MLflow
mlflow.log_params(
    {"dvc_data_version": VERSION, "pixel_mean": pixel_mean, "pixel_std": pixel_std}
)
```

**CLI:**

```bash
# Download specific version
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    --rev fashion-mnist-v1.0.0 \
    -o ./data/
```

### Running Embeddings Pipeline

The embeddings pipeline requires pgvector and Ray:

```bash
# Start Ray
ray start --head

# Set database credentials
export PGVECTOR_HOST=localhost
export PGVECTOR_PASSWORD=admin
# ... other PGVECTOR_* vars

# Run pipeline
cd pipelines/opencloudhub-readmes-embeddings
python run_pipeline.py
```

### Quick Bootstrap for Local Development

If you're using the [local-compose-stack](https://github.com/OpenCloudHub/local-compose-stack) and just want to quickly get all datasets available for testing ML training repos or experimenting with DVC, use the bootstrap script:

```bash
# 1. Source environment variables
set -a && source .env.docker && set +a
unset AWS_CA_BUNDLE  # Fix for some container environments

# 2. Run bootstrap (downloads, processes, versions all datasets)
./scripts/bootstrap-data-examples.sh

# Or include embeddings pipeline (requires pgvector running)
./scripts/bootstrap-data-examples.sh --with-embeddings

# Force re-run even if data exists
./scripts/bootstrap-data-examples.sh --force
```

This script will:

1. Run all data pipelines (emotion, fashion-mnist, wine-quality, opencloudhub-readmes)
1. Push processed data to MinIO
1. Create `v1.0.0` git tags for each dataset
1. Optionally generate embeddings and store in pgvector

After bootstrap, you can immediately use the data in other ML repos:

```bash
# From any training repo
dvc get https://github.com/OpenCloudHub/data-registry \
    data/fashion-mnist/processed \
    --rev fashion-mnist-v1.0.0
```

**Reset for Demo:**

To start fresh (e.g., for recording a demo), use the reset script:

```bash
./scripts/reset-for-demo.sh  # Clears DVC cache, deletes tags
./scripts/bootstrap-data-examples.sh --with-embeddings  # Run fresh
```

______________________________________________________________________

<h2 id="configuration">⚙️ Configuration</h2>

### DVC Remotes

```ini
# .dvc/config
[core]
    remote = minikube

['remote "minikube"']
    url = s3://dvcstore
    endpointurl = https://minio-api.internal.opencloudhub.org

['remote "docker"']
    url = s3://dvcstore
    endpointurl = http://localhost:9000
```

Switch between remotes:

```bash
dvc remote default docker    # Local development
dvc remote default minikube  # Kubernetes
```

### Pipeline Parameters

Each pipeline has a `params.yaml`:

```yaml
# pipelines/fashion-mnist/params.yaml
download:
  base_url: "http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/"

process:
  val_split: 0.1
  random_seed: 42

analyze:
  compute_pixel_stats: true
```

### Embeddings Pipeline Parameters

```python
# pipelines/opencloudhub-readmes-embeddings/params.py
DVC_DATA_VERSION = "opencloudhub-readmes-v1.0.0"
DVC_DATA_PATH = "data/opencloudhub-readmes/raw"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CHUNK_SIZE = 800
EMBEDDING_CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 8
```

______________________________________________________________________

<h2 id="design-decisions">💭 Design Decisions</h2>

### Why Combined Pipelines + Data?

**In this demo:** Pipeline code and data versioning are in the same repository for simplicity.

**In production**, you might separate them:

- **Pipeline code** — In each ML repo (closer to training logic)
- **Data registry** — Only stores `dvc.lock` files and coordinates versions

**We combined them because:**

1. Easier to understand the complete data flow
1. Single repository to demonstrate all DVC patterns
1. Reduces cross-repo complexity for thesis demonstration

### Why Not One Container Per Pipeline?

**In this demo:** All pipelines use the same Docker image with all dependencies.

**In production**, you might:

- Use separate images per pipeline (smaller, faster builds)
- Share only common base layers
- Have specialized images (e.g., GPU for embeddings)

**We used one image because:**

1. Simpler CI/CD configuration
1. Demonstrates the pattern without multi-image complexity
1. Dependencies overlap significantly for demo datasets

### Why Git Tags for Versions?

Alternatives considered:

- **DVC tags** — DVC has its own tagging, but less integrated with Git workflows
- **Branch per version** — Creates branch sprawl, harder to navigate
- **Commit SHAs** — Not human-readable

**Git tags win because:**

1. Semantic versioning (`fashion-mnist-v1.0.0`) is clear
1. Works with standard Git tooling
1. GitHub releases can document changes
1. Training code uses familiar `--rev` pattern

### Why metadata.json in Git (not DVC)?

The `cache: false` option keeps metadata in Git:

```yaml
metrics:
  - ../../data/fashion-mnist/metadata.json:
      cache: false  # Git-tracked, not DVC-tracked
```

**Benefits:**

- Visible in GitHub without downloading data
- Easy to compare across versions (`git diff`)
- Small file size (appropriate for Git)
- DVC metrics commands still work

______________________________________________________________________

<h2 id="contributing">👥 Contributing</h2>

Contributions welcome! See [Contributing Guidelines](https://github.com/opencloudhub/.github/blob/main/.github/CONTRIBUTING.md).

______________________________________________________________________

<h2 id="license">📄 License</h2>

Apache 2.0 License. See [LICENSE](LICENSE).

______________________________________________________________________

<h2 id="acknowledgements">🙏 Acknowledgements</h2>

- [DVC](https://dvc.org/) — Data version control
- [Ray Data](https://docs.ray.io/en/latest/data/data.html) — Distributed data processing
- [MinIO](https://min.io/) — S3-compatible object storage
- [sentence-transformers](https://www.sbert.net/) — Embedding generation
- [pgvector](https://github.com/pgvector/pgvector) — Vector similarity search
- [Argo Workflows](https://argoproj.github.io/workflows/) — Kubernetes workflow orchestration

<p align="right">(<a href="#readme-top">back to top</a>)</p>
