#!/usr/bin/env bash
set -e

# ==============================================================================
# Bootstrap Data Registry
# ==============================================================================
#
# Initializes all example datasets with fixed version tags (v1.0.0) so that
# demo applications can reference a consistent data version. Run this locally as alternative
# to using GitHub action to trigger argo data pipeline workflows running on cluster.
#
# This script:
#   1. Runs all data pipelines (optionally forced)
#   2. Pushes data to MinIO
#   3. Creates v1.0.0 tags for all datasets
#   4. Optionally runs embeddings pipeline
#
# Prerequisites:
#   - Environment variables: source .env.mikikube (or .env.local)
#   - Port-forward pgvector if using minikube(for embeddings):
#       kubectl port-forward -n storage svc/demo-app-db-cluster-rw 5432:5432
#
# Usage:
#   ./scripts/bootstrap-data-examples.sh [--force] [--with-embeddings]
#
# ==============================================================================

FORCE_RUN=false
WITH_EMBEDDINGS=false

for arg in "$@"; do
  case $arg in
    --force) FORCE_RUN=true ;;
    --with-embeddings) WITH_EMBEDDINGS=true ;;
  esac
done

FORCE_FLAG=""
[ "$FORCE_RUN" = true ] && FORCE_FLAG="--force"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 Bootstrap Data Registry (v1.0.0)"
[ "$FORCE_RUN" = true ] && echo "   ⚠️  Force mode enabled"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# ------------------------------------------------------------------------------
# Run all pipelines
# ------------------------------------------------------------------------------
echo "📊 Running all pipelines${FORCE_FLAG:+ (forced)}..."
echo "────────────────────────────────────────────────────────────────────────────────"

PIPELINES=(
  "emotion"
  "fashion-mnist"
  "wine-quality"
  "opencloudhub-readmes-download"
)

for pipeline in "${PIPELINES[@]}"; do
  echo "  → ${pipeline}..."
  dvc repro $FORCE_FLAG pipelines/"${pipeline}"/dvc.yaml
  echo "     ✓ done"
done

echo "  → Adding RAG evaluation questions..."
dvc add data/opencloudhub-readmes/rag-evaluation/questions.csv
echo "     ✓ done"

echo ""

# ------------------------------------------------------------------------------
# Push to MinIO
# ------------------------------------------------------------------------------
echo "📤 Pushing to MinIO..."
echo "────────────────────────────────────────────────────────────────────────────────"
dvc push
echo "   ✓ Data pushed"
echo ""

# ------------------------------------------------------------------------------
# Create v1.0.0 tags
# ------------------------------------------------------------------------------
echo "🏷️  Creating v1.0.0 tags..."
echo "────────────────────────────────────────────────────────────────────────────────"

DATASETS=("emotion" "fashion-mnist" "wine-quality" "opencloudhub-readmes" "opencloudhub-readmes-rag-evaluation" "roco-radiology")

for dataset in "${DATASETS[@]}"; do
  TAG="${dataset}-v1.0.0"
  git tag -d "$TAG" 2>/dev/null || true
  git tag -a "$TAG" -m "${dataset} v1.0.0 (bootstrap)"
  echo "   ✓ ${TAG}"
done

echo ""

# ------------------------------------------------------------------------------
# Commit and push
# ------------------------------------------------------------------------------
echo "💾 Committing and pushing..."
echo "────────────────────────────────────────────────────────────────────────────────"
git add .
git commit -m "chore: bootstrap data registry v1.0.0 [skip ci]" || echo "   ℹ️  No changes"
git push origin main --force || echo "   ℹ️  Nothing to push"
git push origin --tags --force || echo "   ℹ️  No tags to push"
echo ""

# ------------------------------------------------------------------------------
# Embeddings (optional)
# ------------------------------------------------------------------------------
if [ "$WITH_EMBEDDINGS" = true ]; then
  echo "🧠 Running embeddings pipeline..."
  echo "────────────────────────────────────────────────────────────────────────────────"
  sed -i 's/^DVC_DATA_VERSION = .*/DVC_DATA_VERSION = "opencloudhub-readmes-v1.0.0"/' pipelines/opencloudhub-readmes-embeddings/params.py
  dvc repro $FORCE_FLAG pipelines/opencloudhub-readmes-embeddings/dvc.yaml

  # Create embeddings tag
  TAG="opencloudhub-readmes-embeddings-v1.0.0"
  git tag -d "$TAG" 2>/dev/null || true
  git tag -a "$TAG" -m "opencloudhub-readmes-embeddings v1.0.0 (bootstrap)"
  echo "   ✓ Created tag: ${TAG}"

  git add .
  git commit -m "chore: embeddings for v1.0.0 [skip ci]" || true
  git push origin main --force || true
  git push origin --tags --force || true
  echo "   ✓ Embeddings done"
  echo ""
fi

# ------------------------------------------------------------------------------
# Done
# ------------------------------------------------------------------------------
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Bootstrap complete! All datasets tagged as v1.0.0"
echo ""
echo "📦 Use in your apps:"
echo "   dvc get https://github.com/OpenCloudHub/data-registry data/emotion --rev emotion-v1.0.0"
echo "════════════════════════════════════════════════════════════════════════════════"
