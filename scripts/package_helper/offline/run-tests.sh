set -euo pipefail
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
pytest -q
