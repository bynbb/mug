$ErrorActionPreference = "Stop"
param(
  [ValidateSet("linux","win","mac")] [string]$Platform = "linux",
  [string]$WheelDir = ""
)
$env:PIP_NO_INDEX = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
if (-not $WheelDir) { $WheelDir = "dist/$Platform" }
$req = "requirements-offline-$Platform.txt"
python -m pip install --upgrade pip
if (Test-Path $req) {
  python -m pip install --no-index --find-links "$WheelDir" -r $req
} else {
  $wheels = Get-ChildItem "$WheelDir" -Filter *.whl -File | ForEach-Object FullName
  if ($wheels.Count -eq 0) { throw "No wheels found in $WheelDir" }
  python -m pip install --no-index --find-links "$WheelDir" @wheels
}
