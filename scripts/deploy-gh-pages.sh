#!/usr/bin/env bash
# ==============================================================================
# Script: deploy-gh-pages.sh
# Purpose: Deploys the Kairi & Co. static storefront mockup directly to the 
#          gh-pages branch of the repository without polluting working tree.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/src/client/static-mockup"
BRANCH_NAME="gh-pages"

echo "=== Packaging Kairi & Co. Static Mockup for GitHub Pages (${BRANCH_NAME}) ==="

if [ ! -d "${SOURCE_DIR}" ]; then
  echo "Error: Source directory '${SOURCE_DIR}' does not exist." >&2
  exit 1
fi

TEMP_DIR="$(mktemp -d)"
echo "Staging static files in isolated directory: ${TEMP_DIR}"
cp -R "${SOURCE_DIR}/"* "${TEMP_DIR}/"
cp "${SOURCE_DIR}/.nojekyll" "${TEMP_DIR}/" 2>/dev/null || touch "${TEMP_DIR}/.nojekyll"

# Initialize isolated git repo to construct a pure gh-pages commit
cd "${TEMP_DIR}"
git init -q
git config user.name "Kairi Deployer"
git config user.email "deploy@kairi-co.local"
git checkout -q -b "${BRANCH_NAME}"
git add -A
git commit -q -m "Deploy Kairi & Co. Storefront Mockup to GitHub Pages [skip ci]"

# Force push into local repository's gh-pages branch
echo "Updating local branch '${BRANCH_NAME}'..."
git push -q "${REPO_ROOT}" "${BRANCH_NAME}:${BRANCH_NAME}" --force

cd "${REPO_ROOT}"
rm -rf "${TEMP_DIR}"

echo "✓ Branch '${BRANCH_NAME}' has been cleanly updated locally."

# Automatically push to origin if requested or prompt
if [ "${1:-}" = "--push" ] || [ "${1:-}" = "-p" ]; then
  echo "Pushing branch '${BRANCH_NAME}' to remote origin..."
  git push origin "${BRANCH_NAME}" --force
  echo "✓ Pushed to origin/${BRANCH_NAME} successfully!"
else
  echo "To push to GitHub, run:"
  echo "  git push origin ${BRANCH_NAME} --force"
  echo "Or re-run this script with --push flag:"
  echo "  ./scripts/deploy-gh-pages.sh --push"
fi

echo "=== Deployment package ready ==="
