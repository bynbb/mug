set -euo pipefail
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
PLATFORM="${PLATFORM:-linux}"
WHEEL_DIR="${WHEEL_DIR:-dist/$PLATFORM}"
REQ="requirements-offline-$PLATFORM.txt"
python -m pip install --upgrade pip
if [ -f "$REQ" ]; then
  python -m pip install --no-index --find-links "$WHEEL_DIR" -r "$REQ"
else
  python -m pip install --no-index --find-links "$WHEEL_DIR" "$WHEEL_DIR"/*.whl
fi
