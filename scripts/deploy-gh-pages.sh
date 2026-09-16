#!/usr/bin/env bash
# ==============================================================================
# Script: deploy-gh-pages.sh
# Purpose: Deploys the Kairi & Co. static storefront mockup directly to the 
#          gh-pages branch of the repository.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/src/client/static-mockup"
BRANCH_NAME="gh-pages"

echo "=== Deploying Kairi & Co. Static Mockup to GitHub Pages (${BRANCH_NAME}) ==="

if [ ! -d "${SOURCE_DIR}" ]; then
  echo "Error: Source directory '${SOURCE_DIR}' does not exist." >&2
  exit 1
fi

TEMP_DIR="$(mktemp -d)"
echo "Staging static files in temporary directory: ${TEMP_DIR}"
cp -R "${SOURCE_DIR}/"* "${TEMP_DIR}/"

cd "${REPO_ROOT}"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Current working branch: ${CURRENT_BRANCH}"

# Create or switch to gh-pages branch as an orphan or update existing
if git show-ref --quiet --heads "${BRANCH_NAME}"; then
  echo "Branch '${BRANCH_NAME}' exists locally. Checking it out..."
  git checkout "${BRANCH_NAME}"
else
  echo "Creating orphan branch '${BRANCH_NAME}'..."
  git checkout --orphan "${BRANCH_NAME}"
fi

# Clean out old working directory files
git rm -rf . > /dev/null 2>&1 || true

# Copy static files to the root of gh-pages branch
cp -R "${TEMP_DIR}/"* ./

# Add .nojekyll so GitHub Pages does not ignore files or parse Jekyll
touch .nojekyll

git add .
git commit -m "Deploy Kairi & Co. Storefront Mockup to GitHub Pages [skip ci]" || echo "No changes to commit."

echo "Branch '${BRANCH_NAME}' updated locally."
echo "To push to GitHub remote, run:"
echo "  git push origin ${BRANCH_NAME} --force"

# Switch back to original branch
git checkout "${CURRENT_BRANCH}"
rm -rf "${TEMP_DIR}"

echo "=== Mockup deployment staging complete. Returned to branch: ${CURRENT_BRANCH} ==="
