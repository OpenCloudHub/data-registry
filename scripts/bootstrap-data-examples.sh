#!/usr/bin/env bash
set -e

# ==============================================================================
# Bootstrap Data Registry
# ==============================================================================
#
# Initializes all example datasets with fixed version tags (v1.0.0) so that
# demo applications can reference a consistent data version. Run this if you are unable
# to test via GH action workflows
#
# This script:
#   1. Force-runs all data pipelines (ignores DVC cache)
#   2. Pushes data to MinIO
#   3. Creates v1.0.0 tags for all datasets
#   4. Optionally runs embeddings pipeline
#
# Prerequisites:
#   - Environment variables: source .env
#   - Port-forward pgvector (for embeddings):
#       kubectl port-forward -n storage svc/demo-app-db-cluster-rw 5432:5432
#
# Usage:
#   ./scripts/bootstrap-data-examples.sh [--with-embeddings]
#
# ==============================================================================

WITH_EMBEDDINGS=true
[ "$1" = "--with-embeddings" ] && WITH_EMBEDDINGS=true

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 Bootstrap Data Registry (v1.0.0)"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# ------------------------------------------------------------------------------
# Force run all pipelines
# ------------------------------------------------------------------------------
echo "📊 Running all pipelines (forced)..."
echo "────────────────────────────────────────────────────────────────────────────────"

PIPELINES=(
  "emotion"
  "fashion-mnist"
  "wine-quality"
  "opencloudhub-readmes-download"
)

for pipeline in "${PIPELINES[@]}"; do
  echo "  → ${pipeline}..."
  dvc repro --force pipelines/"${pipeline}"/dvc.yaml
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

DATASETS=("emotion" "fashion-mnist" "wine-quality" "opencloudhub-readmes" "opencloudhub-readmes-rag-evaluation")

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
  sed -i 's/version: ".*"/version: "opencloudhub-readmes-v1.0.0"/' pipelines/opencloudhub-readmes-embeddings/params.yaml
  dvc repro --force pipelines/opencloudhub-readmes-embeddings/dvc.yaml
  
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