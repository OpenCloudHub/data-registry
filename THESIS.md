# Thesis Context: Data Registry

## Role in Platform Architecture

The Data Registry sits at **Layer 2 (Data Management)** of the MLOps platform, serving as the central hub for versioned datasets that feed into all ML training workloads.

```
Layer 1: Infrastructure     → Kubernetes, MinIO, PostgreSQL, MLflow, Ray, Argo
Layer 2: Data Management    → THIS REPOSITORY (DVC pipelines, versioned datasets)
Layer 3: ML Workloads       → Training jobs consuming versioned data
```

This repository demonstrates how to:

- Version large datasets using DVC + Git tags
- Build reproducible data pipelines (Download → Process → Analyze)
- Generate embeddings for RAG systems using Ray Data
- Integrate with MLflow Prompt Registry for instruction management

## Requirements Demonstrated

| Requirement                     | How This Repo Addresses It                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------------- |
| **FR3: Data Versioning**        | DVC with git tags for immutable dataset snapshots (`dvc.yaml`, `dvc.lock`)                        |
| **FR4: Data Lineage**           | Metadata files track source version, model, parameters (`metadata.json`)                          |
| **FR5: Reproducibility**        | Version-pinned data access via `dvc get --rev tag-name`                                           |
| **FR7: Distributed Processing** | Ray Data for scalable embeddings (`pipelines/opencloudhub-readmes-embeddings/scripts/process.py`) |
| **FR9: MLflow Integration**     | Prompt Registry for VLM instructions (`pipelines/roco-radiology/scripts/process.py`)              |
| **FR12: GitOps Automation**     | GitHub Actions → Argo Workflows (`.github/workflows/`)                                            |
| **NFR2: Scalability**           | Ray Data batched processing, HNSW indexing for vectors                                            |
| **NFR4: Portability**           | Environment-based config (`.env.docker`, `.env.minikube`)                                         |

## Key Implementation Patterns

1. **DVC + Git Tags Pattern** (`pipelines/*/dvc.yaml`)

   - Data versions tied to git tags enable training code to reference exact dataset snapshots
   - `dvc.lock` captures exact MD5 hashes of all pipeline outputs
   - Tags like `fashion-mnist-v1.0.0` create immutable data references

1. **Metadata as Metrics** (`pipelines/*/scripts/analyze.py`)

   - Statistics computed at pipeline completion (pixel means, class distributions)
   - Tracked by DVC for drift monitoring
   - Consumed by training jobs for normalization parameters

1. **Environment-based Configuration** (`.env.docker`, `.env.minikube`)

   - Secrets via environment variables (never in git)
   - Same code runs locally or on cluster
   - DVC remotes switch between `docker` and `minikube`

1. **Ray Data for Scale** (`pipelines/opencloudhub-readmes-embeddings/scripts/process.py`)

   - Distributed processing with batched embedding generation
   - Parallel database writes with connection pooling
   - GPU acceleration when available

1. **MLflow Prompt Registry** (`pipelines/roco-radiology/scripts/process.py`)

   - Version-controlled prompts for VLM training data preparation
   - Enables A/B testing of different instruction formats
   - Full lineage: prompt version stored in dataset metadata

1. **Production Pipeline Wrapper** (`pipelines/opencloudhub-readmes-embeddings/run_pipeline.py`)

   - Runtime parameter injection from environment
   - Change detection via `dvc.lock` hash comparison
   - Conditional tagging (only when new outputs produced)

## Key Files Reference

| File                                                           | Purpose                              |
| -------------------------------------------------------------- | ------------------------------------ |
| `pipelines/fashion-mnist/dvc.yaml`                             | Standard 3-stage pipeline definition |
| `pipelines/opencloudhub-readmes-embeddings/scripts/process.py` | Ray Data embeddings pipeline         |
| `pipelines/roco-radiology/scripts/process.py`                  | MLflow Prompt Registry integration   |
| `.github/workflows/run-data-pipelines.yaml`                    | GitHub Actions → Argo Workflows      |
| `scripts/bootstrap-data-examples.sh`                           | Local initialization script          |
| `.dvc/config`                                                  | DVC remote configuration             |

## Video Demonstrations

- **Data Pipeline Execution**: Shows `dvc repro` running locally and on cluster
- **Embeddings Pipeline**: Demonstrates Ray Data distributed processing
- **Data Versioning**: Shows how training code references specific versions
- **Argo Workflow**: Production pipeline with auto-versioning

## Thesis Chapter References

- **Design & Implementation (Ch4)**:

  - Section 4.4: Data Pipeline Architecture
  - Section 4.5: DVC + Git Integration
  - Section 4.8: Embeddings Pipeline with Ray Data

- **Evaluation (Ch6)**:

  - Section 6.2: Data Pipeline Performance
  - Section 6.4: Reproducibility Validation

## Integration with Other Repositories

```
data-registry (this repo)
    │
    ├──► ai-ml-sklearn     (consumes fashion-mnist, wine-quality)
    ├──► ai-dl-bert        (consumes emotion dataset)
    ├──► ai-radiology-qwen (consumes roco-radiology)
    └──► demo-app-genai    (uses embeddings via pgvector)
```

Training jobs consume data via:

```python
import dvc.api

# Get versioned data URL
url = dvc.api.get_url(
    "data/fashion-mnist/processed/train/train.parquet",
    repo="https://github.com/OpenCloudHub/data-registry",
    rev="fashion-mnist-v1.0.0",
)

# Load with Ray Data
ds = ray.data.read_parquet(url, filesystem=s3_fs)
```
