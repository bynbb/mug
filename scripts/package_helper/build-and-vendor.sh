#!/usr/bin/env bash
set -euo pipefail

# Go to repo root
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Fresh dist/
mkdir -p dist

# Build venv for isolation
VENV_DIR="$REPO_ROOT/.venv_build"
if [[ ! -d "$VENV_DIR" ]]; then
  python -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

pip install -U pip wheel build >/dev/null

echo "🛠️  Building (wheel + sdist)..."
python -m build

REQ_FILE="dist/runtime-requirements.txt"
python - <<'PY' | tee "$REQ_FILE" >/dev/null
import sys
try:
    import tomllib as toml  # py311+
except ModuleNotFoundError:
    import toml
data = toml.load('pyproject.toml')
deps = (data.get('project', {}) or {}).get('dependencies', []) or []
for d in deps:
    d = str(d).strip()
    if d:
        print(d)
PY

if [[ -s "$REQ_FILE" ]]; then
  echo "⬇️  Downloading runtime wheels into dist/..."
  pip download --only-binary=:all: --dest dist -r "$REQ_FILE"
else
  echo "ℹ️  No runtime deps found in [project].dependencies."
fi

echo
echo "✅ dist/ ready:"
ls -1 dist
