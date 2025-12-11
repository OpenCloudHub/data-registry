#!/usr/bin/env bash
set -e

# ==============================================================================
# Reset Data Registry for Demo
# ==============================================================================
#
# Cleans up DVC state and git tags to run bootstrap-data-examples.sh
# fresh for a demo.
#
# Usage:
#   ./scripts/reset-for-demo.sh
#
# ==============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🧹 Resetting Data Registry for Demo"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# ------------------------------------------------------------------------------
# Delete all v1.0.0 tags (local and remote)
# ------------------------------------------------------------------------------
echo "🏷️  Deleting v1.0.0 tags..."
echo "────────────────────────────────────────────────────────────────────────────────"

TAGS=(
  "emotion-v1.0.0"
  "fashion-mnist-v1.0.0"
  "wine-quality-v1.0.0"
  "opencloudhub-readmes-download-v1.0.0"
  "opencloudhub-readmes-rag-evaluation-v1.0.0"
  "opencloudhub-readmes-embeddings-v1.0.0"
  "roco-radiology-v1.0.0"
)

for tag in "${TAGS[@]}"; do
  # Delete local tag
  git tag -d "$tag" 2>/dev/null && echo "   ✓ Deleted local: $tag" || true
  # Delete remote tag
  git push origin --delete "$tag" 2>/dev/null && echo "   ✓ Deleted remote: $tag" || true
done

echo ""

# ------------------------------------------------------------------------------
# Clear DVC cache and locks
# ------------------------------------------------------------------------------
echo "🗑️  Clearing DVC cache and locks..."
echo "────────────────────────────────────────────────────────────────────────────────"

rm -rf .dvc/cache .dvc/tmp .dvc/lock
find . -name "dvc.lock" -delete
echo "   ✓ DVC cache cleared"
echo "   ✓ DVC lock files deleted"

echo ""

# ------------------------------------------------------------------------------
# Clean data folder (optional - uncomment if you want fresh downloads)
# ------------------------------------------------------------------------------
echo "📁 Cleaning data folder..."
echo "────────────────────────────────────────────────────────────────────────────────"

# Keep the folder structure but remove data files
rm -rf data/emotion/raw data/emotion/processed data/emotion/metadata.json
rm -rf data/fashion-mnist/raw data/fashion-mnist/processed data/fashion-mnist/metadata.json
rm -rf data/wine-quality/raw data/wine-quality/processed data/wine-quality/metadata.json
rm -rf data/opencloudhub-readmes-download/raw
rm -rf data/opencloudhub-readmes-embeddings
rm -f data/opencloudhub-readmes-rag-evaluation/questions.csv.dvc

echo "   ✓ Data folders cleaned"

echo ""

# ------------------------------------------------------------------------------
# Done
# ------------------------------------------------------------------------------
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Reset complete! Ready for demo."
echo ""
echo "📹 Now run:"
echo "   ./scripts/bootstrap-data-examples.sh --with-embeddings"
echo "════════════════════════════════════════════════════════════════════════════════"
