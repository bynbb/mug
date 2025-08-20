#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

scripts/build-and-vendor.sh
scripts/make-zip.sh  # uses HEAD -> obk_clean.zip
