#!/usr/bin/env bash
set -euo pipefail

REF="${1:-HEAD}"
ZIP_NAME="${2:-}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ -z "$ZIP_NAME" ]]; then
  if [[ "$REF" == "HEAD" ]]; then
    ZIP_NAME="obk_clean.zip"
  else
    SAFE_REF="$(echo "$REF" | sed 's/[^A-Za-z0-9._-]/_/g')"
    ZIP_NAME="obk_${SAFE_REF}.zip"
  fi
fi

echo "📦 Creating base archive from ${REF} -> ${ZIP_NAME}"
git archive --format=zip --output "$ZIP_NAME" "$REF"

# Add ./dist if present
if [[ -d "dist" ]]; then
  echo "➕ Including ./dist/ in ${ZIP_NAME}"
  # Add recursively; keep paths
  zip -r "$ZIP_NAME" dist >/dev/null
else
  echo "ℹ️  No dist/ directory found; skipping."
fi

echo
echo "✅ Done -> $ZIP_NAME"
