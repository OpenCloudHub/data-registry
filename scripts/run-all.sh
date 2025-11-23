#!/usr/bin/env bash
set -e  # Exit on error

# ==============================================================================
# Run all data pipelines and create versioned tags
# ==============================================================================
# This script:
# 1. Runs all DVC data processing pipelines
# 2. Pushes data to remote storage (MinIO/S3)
# 3. Creates Git tags for versioned dataset releases
# 4. Commits and pushes changes to Git
# ==============================================================================

VERSION="v1.0.0"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 Data Registry Pipeline Execution"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Version: ${VERSION}"
echo ""

# ------------------------------------------------------------------------------
# Step 1: Run Data Processing Pipelines
# ------------------------------------------------------------------------------
echo "📊 Step 1/5: Running data processing pipelines..."
echo "────────────────────────────────────────────────────────────────────────────────"

echo "  → Processing emotion dataset..."
dvc repro pipelines/emotion/dvc.yaml
echo "     ✓ Emotion dataset complete"

echo "  → Processing fashion-mnist dataset..."
dvc repro pipelines/fashion-mnist/dvc.yaml
echo "     ✓ Fashion-MNIST dataset complete"

echo "  → Processing wine-quality dataset..."
dvc repro pipelines/wine-quality/dvc.yaml
echo "     ✓ Wine Quality dataset complete"

echo "  → Downloading opencloudhub-readmes..."
dvc repro pipelines/opencloudhub-readmes-download/dvc.yaml
echo "     ✓ OpenCloudHub READMEs downloaded"

echo "  → Adding RAG evaluation questions..."
dvc add data/opencloudhub-readmes/rag-evaluation/questions.csv
echo "     ✓ RAG evaluation questions added"

echo ""

# ------------------------------------------------------------------------------
# Step 2: Push Data to Remote Storage
# ------------------------------------------------------------------------------
echo "📤 Step 2/5: Pushing data to remote storage (MinIO)..."
echo "────────────────────────────────────────────────────────────────────────────────"
dvc push
echo "   ✓ All datasets pushed to remote storage"
echo ""

# ------------------------------------------------------------------------------
# Step 3: Create Git Tags for Dataset Versions
# ------------------------------------------------------------------------------
echo "🏷️  Step 3/5: Creating dataset version tags..."
echo "────────────────────────────────────────────────────────────────────────────────"

DATASETS=(
  "fashion-mnist"
  "wine-quality"
  "emotion"
  "opencloudhub-readmes"
  "opencloudhub-readmes-rag-evaluation"
)

for dataset in "${DATASETS[@]}"; do
  TAG="${dataset}-${VERSION}"
  git tag -f "${TAG}" -m "${dataset} ${VERSION}"
  echo "   ✓ Created tag: ${TAG}"
done
echo ""

# ------------------------------------------------------------------------------
# Step 4: Push Tags to GitHub
# ------------------------------------------------------------------------------
echo "📤 Step 4/5: Pushing tags to GitHub..."
echo "────────────────────────────────────────────────────────────────────────────────"
git push -f origin --tags
echo "   ✓ All tags pushed to GitHub"
echo ""

# ------------------------------------------------------------------------------
# Step 5: Commit and Push Changes
# ------------------------------------------------------------------------------
echo "💾 Step 5/5: Committing and pushing changes..."
echo "────────────────────────────────────────────────────────────────────────────────"
git add .
git commit -m "chore: update datasets to ${VERSION}" || echo "   ℹ️  No changes to commit"
git push
echo "   ✓ Changes pushed to GitHub"
echo ""

# ------------------------------------------------------------------------------
# Step 6: Run Embeddings Pipeline (Requires Committed Tags)
# ------------------------------------------------------------------------------
echo "🧠 Running embeddings pipeline..."
echo "────────────────────────────────────────────────────────────────────────────────"
echo "   ℹ️  This step requires the tags to be committed and pushed first"
echo "   → Processing README embeddings and storing in pgvector..."
dvc repro pipelines/opencloudhub-readmes-embeddings/dvc.yaml
echo "   ✓ Embeddings pipeline complete"
echo ""

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ All pipelines completed successfully!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📦 Datasets tagged and published:"
for dataset in "${DATASETS[@]}"; do
  echo "   • ${dataset}-${VERSION}"
done
echo ""
echo "🔗 View releases: https://github.com/OpenCloudHub/data-registry/tags"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""