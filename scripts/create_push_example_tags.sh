#!/usr/bin/env bash

# Set the version you want to use
VERSION="v1.0.0"

# Push data to remote repository
dvc push

# Create tags for all datasets
for dataset in fashion-mnist wine-quality emotion opencloudhub-readmes; do
  git tag -f "${dataset}-${VERSION}" -m "${dataset} ${VERSION}"
done

# Push all tags at once
git push -f origin fashion-mnist-${VERSION} wine-quality-${VERSION} emotion-${VERSION} opencloudhub-readmes-${VERSION}

# Or push all tags matching the pattern
git push -f origin --tags

echo "✅ Created and pushed tags:"
echo "  - fashion-mnist-${VERSION}"
echo "  - wine-quality-${VERSION}"
echo "  - emotion-${VERSION}"