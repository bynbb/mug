$ErrorActionPreference = "Stop"
$env:PIP_NO_INDEX = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
pytest -q
