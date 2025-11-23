#!/usr/bin/env bash
VERSION="v1.0.0"

echo "🚀 Running all data pipelines..."

dvc repro pipelines/emotion/dvc.yaml
dvc repro pipelines/fashion-mnist/dvc.yaml
dvc repro pipelines/wine-quality/dvc.yaml
dvc repro pipelines/opencloudhub-readmes-download/dvc.yaml
dvc add data/opencloudhub-readmes/rag-evaluation/questions.csv

git add .
git commit -m "Update opencloudhub-readmes data"
git push


# Here we need to commit first and create a tag before running the embeddings pipeline
dvc repro pipelines/opencloudhub-readmes-embeddings/dvc.yaml