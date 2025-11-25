#!/usr/bin/env bash
set -e

# ==============================================================================
# Run all data pipelines and create versioned tags
# ==============================================================================

BUMP_TYPE="${BUMP_TYPE:-patch}"
IS_CRON="${IS_CRON:-false}"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 Data Registry Pipeline Execution"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "Bump type: ${BUMP_TYPE}"
echo "Is cron: ${IS_CRON}"
echo ""

# ------------------------------------------------------------------------------
# Run all pipelines
# ------------------------------------------------------------------------------
echo "📊 Running data processing pipelines..."
echo "────────────────────────────────────────────────────────────────────────────────"

PIPELINES=(
  "emotion"
  "fashion-mnist"
  "wine-quality"
  "opencloudhub-readmes-download"
)

for pipeline in "${PIPELINES[@]}"; do
  echo "  → Processing ${pipeline}..."
  dvc repro pipelines/${pipeline}/dvc.yaml
  echo "     ✓ ${pipeline} complete"
done

echo "  → Adding RAG evaluation questions..."
dvc add data/opencloudhub-readmes/rag-evaluation/questions.csv 2>/dev/null || echo "     ℹ️  Already tracked"
echo "     ✓ RAG evaluation questions processed"

echo ""

# ------------------------------------------------------------------------------
# Detect which datasets changed using dvc diff
# ------------------------------------------------------------------------------
echo "🔍 Detecting changed datasets..."
echo "────────────────────────────────────────────────────────────────────────────────"

DVC_DIFF=$(dvc diff --json HEAD 2>/dev/null || echo '{"added":[],"deleted":[],"modified":[],"renamed":[]}')

CHANGED_DATASETS=$(echo "$DVC_DIFF" | python3 -c "
import sys, json
try:
    diff = json.load(sys.stdin)
    datasets = set()
    
    for change_type in ['added', 'modified']:
        for item in diff.get(change_type, []):
            path = item.get('path', '')
            if path.startswith('data/'):
                parts = path.split('/')
                if len(parts) >= 2:
                    datasets.add(parts[1])
    
    for item in diff.get('renamed', []):
        new_path = item.get('path', {}).get('new', '')
        if new_path.startswith('data/'):
            parts = new_path.split('/')
            if len(parts) >= 2:
                datasets.add(parts[1])
    
    for ds in sorted(datasets):
        print(ds)
except:
    pass
")

if [ -z "$CHANGED_DATASETS" ]; then
  echo "  ℹ️  No datasets changed - skipping push and tagging"
  exit 0
fi

# Show what changed
while IFS= read -r dataset; do
  [ -n "$dataset" ] && echo "  ✓ Changes detected: ${dataset}"
done <<< "$CHANGED_DATASETS"

echo ""

# ------------------------------------------------------------------------------
# Push data to remote storage
# ------------------------------------------------------------------------------
echo "📤 Pushing data to remote storage..."
echo "────────────────────────────────────────────────────────────────────────────────"
dvc push
echo "   ✓ Data pushed to MinIO"
echo ""

# ------------------------------------------------------------------------------
# Create tags only for changed datasets
# ------------------------------------------------------------------------------
echo "🏷️  Creating tags for changed datasets..."
echo "────────────────────────────────────────────────────────────────────────────────"

while IFS= read -r dataset; do
  [ -z "$dataset" ] && continue
  
  LATEST_TAG=$(git tag -l "${dataset}-v*" --sort=-version:refname | head -n1)
  
  if [ -z "$LATEST_TAG" ]; then
    NEW_VERSION="1.0.0"
  else
    CURRENT_VERSION=$(echo "$LATEST_TAG" | grep -oP "${dataset}-v\K[0-9]+\.[0-9]+\.[0-9]+" | head -1)
    IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
    
    case $BUMP_TYPE in
      major) NEW_VERSION="$((MAJOR + 1)).0.0" ;;
      minor) NEW_VERSION="${MAJOR}.$((MINOR + 1)).0" ;;
      patch) NEW_VERSION="${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
    esac
  fi
  
  if [ "$IS_CRON" = "true" ]; then
    TAG_NAME="${dataset}-v${NEW_VERSION}-automated"
    TAG_MESSAGE="${dataset} v${NEW_VERSION} (automated)"
  else
    TAG_NAME="${dataset}-v${NEW_VERSION}"
    TAG_MESSAGE="${dataset} v${NEW_VERSION}"
  fi
  
  git tag -a "${TAG_NAME}" -m "${TAG_MESSAGE}"
  echo "   ✓ Created: ${TAG_NAME}"
done <<< "$CHANGED_DATASETS"

echo ""

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Pipeline execution complete!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📦 Tagged datasets:"
while IFS= read -r dataset; do
  [ -n "$dataset" ] && {
    LATEST_TAG=$(git tag -l "${dataset}-v*" --sort=-version:refname | head -n1)
    echo "   • ${LATEST_TAG}"
  }
done <<< "$CHANGED_DATASETS"
echo ""