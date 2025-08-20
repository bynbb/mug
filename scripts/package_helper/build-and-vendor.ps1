<# scripts/build-and-vendor.ps1
    Build/vendor wheels into dist/, then make the wheelhouse “no-internet” friendly:
    - Split wheels by platform into dist/linux, dist/win, dist/mac
    - Generate requirements-offline-*.txt from the *actual* wheels present
    - Verify each folder only contains matching-platform wheels (py3-none-any allowed)
    - (Optional) emit offline helper scripts under scripts/offline/

    You can also optionally download runtime wheels before organizing by providing
    -RuntimeRequirements (a requirements file). By default this script won’t download.

    Examples
      pwsh -File scripts/build-and-vendor.ps1
      pwsh -File scripts/build-and-vendor.ps1 -WriteOfflineScripts
      pwsh -File scripts/build-and-vendor.ps1 -RuntimeRequirements requirements.txt -IncludeLinuxWheels -WriteOfflineScripts
#>

[CmdletBinding()]
param(
  [string] $Dist = "dist",
  [string] $RuntimeRequirements = "",     # optional: if set, pip download wheels first
  [switch] $IncludeLinuxWheels,           # when downloading, also get manylinux wheels
  [switch] $WriteOfflineScripts           # write scripts/offline helpers
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  git rev-parse --show-toplevel
}

function New-Dir($p) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

# ---------------------------------------------------------------------------
# 0) Setup
# ---------------------------------------------------------------------------
$repo = Resolve-RepoRoot
Set-Location $repo

$distRoot = Join-Path $repo $Dist
New-Dir $distRoot

# ---------------------------------------------------------------------------
# 1) (Optional) Download runtime wheels into dist/
# ---------------------------------------------------------------------------
if ($RuntimeRequirements) {
  if (-not (Test-Path $RuntimeRequirements)) {
    throw "Runtime requirements file '$RuntimeRequirements' not found."
  }

  Write-Host "`n==> Downloading runtime wheels into '$Dist'..."
  # Always download native Windows wheels (since you’re invoking from Windows)
  & python -m pip download --only-binary=:all: --dest $distRoot --platform win_amd64 --implementation cp --python-version 3.11 -r $RuntimeRequirements
  if ($LASTEXITCODE) { throw "pip download (win_amd64) failed." }

  if ($IncludeLinuxWheels) {
    # Broad manylinux tag; compatible wheels (e.g., py3-none-any) will download too
    & python -m pip download --only-binary=:all: --dest $distRoot --platform manylinux2014_x86_64 --implementation cp --python-version 3.11 -r $RuntimeRequirements
    if ($LASTEXITCODE) { throw "pip download (manylinux2014_x86_64) failed." }
  }
} else {
  Write-Host "`n(i) Skipping pip downloads (no -RuntimeRequirements provided)."
}

# ---------------------------------------------------------------------------
# 2) Split wheels by platform
# ---------------------------------------------------------------------------
Write-Host "`n==> Splitting wheels by platform..."
$linux = Join-Path $distRoot "linux"
$win   = Join-Path $distRoot "win"
$mac   = Join-Path $distRoot "mac"
New-Dir $linux; New-Dir $win; New-Dir $mac

$wheels = Get-ChildItem -Path $distRoot -Filter *.whl -File
$moveCount = 0
foreach ($whl in $wheels) {
  $n = $whl.Name.ToLowerInvariant()
  $dest = $linux
  if ($n -match 'win(32|_amd64|_arm64)')       { $dest = $win  }
  elseif ($n -match 'macosx')                  { $dest = $mac  }
  elseif ($n -match 'manylinux|musllinux')     { $dest = $linux }
  elseif ($n -match 'py3-none-any')            { $dest = $linux }  # default
  Move-Item -LiteralPath $whl.FullName -Destination (Join-Path $dest $whl.Name) -Force
  $moveCount++
}
Write-Host "Moved $moveCount wheel(s) into:"
Write-Host (" - {0}" -f $linux)
Write-Host (" - {0}" -f $win)
if (Test-Path $mac) { Write-Host (" - {0}" -f $mac) }

# ---------------------------------------------------------------------------
# 3) Generate pinned requirements from actual wheelhouse
# ---------------------------------------------------------------------------
function Write-Pins($folder, $outFile) {
  $map = @{}
  Get-ChildItem -Path $folder -Filter *.whl -File | ForEach-Object {
    $name = $_.BaseName
    $parts = $name -split '-'           # name-version-<tags>
    if ($parts.Length -ge 2) {
      $pkg = ($parts[0] -replace '_','-').ToLowerInvariant()
      $ver = $parts[1]
      $map[$pkg] = $ver
    }
  }
  $lines = ($map.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)==$($_.Value)" })
  if ($lines.Count -gt 0) {
    Set-Content -LiteralPath $outFile -Value $lines -Encoding UTF8
    Write-Host ("Pinned {0} package(s) -> {1}" -f $map.Count, $outFile)
  } else {
    Write-Host ("(i) No wheels in {0}; skipping {1}" -f $folder, $outFile)
  }
}

Write-Host "`n==> Writing pinned requirements..."
$reqLinux = Join-Path $repo "requirements-offline-linux.txt"
$reqWin   = Join-Path $repo "requirements-offline-win.txt"
if ((Get-ChildItem $linux -Filter *.whl -File).Count -gt 0) { Write-Pins $linux $reqLinux }
if ((Get-ChildItem $win   -Filter *.whl -File).Count -gt 0) { Write-Pins $win   $reqWin   }

# ---------------------------------------------------------------------------
# 4) Verify folders contain only matching-platform wheels
# ---------------------------------------------------------------------------
Write-Host "`n==> Verifying wheel folders..."
function Assert-Only($folder, [string[]] $allow) {
  if (-not (Test-Path $folder)) { return }
  $bad = @()
  foreach ($w in (Get-ChildItem $folder -Filter *.whl -File)) {
    $n = $w.Name.ToLowerInvariant()
    $ok = $false
    foreach ($k in $allow) { if ($n.Contains($k)) { $ok = $true; break } }
    if (-not $ok -and -not $n.Contains('py3-none-any')) { $bad += $w.Name }
  }
  if ($bad.Count -gt 0) {
    throw ("{0} contains non-matching wheels:`n  {1}" -f $folder, ($bad -join "`n  "))
  }
  Write-Host ("{0}: OK" -f $folder)   # <- fixed: avoid "$folder: OK" interpolation issue
}
Assert-Only $linux @('manylinux','musllinux')
Assert-Only $win   @('win32','win_amd64','win_arm64')
if (Test-Path $mac) { Assert-Only $mac @('macosx') }

# ---------------------------------------------------------------------------
# 5) (Optional) write offline helper scripts
# ---------------------------------------------------------------------------
if ($WriteOfflineScripts) {
  Write-Host "`n==> Writing offline helper scripts (install/run-tests) ..."
  $off = Join-Path $repo "scripts/offline"
  New-Dir $off

  @'
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
'@ | Set-Content -LiteralPath (Join-Path $off "install.ps1") -Encoding UTF8

  @'
$ErrorActionPreference = "Stop"
$env:PIP_NO_INDEX = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
pytest -q
'@ | Set-Content -LiteralPath (Join-Path $off "run-tests.ps1") -Encoding UTF8

  @'
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
'@ | Set-Content -LiteralPath (Join-Path $off "install-linux.sh") -Encoding UTF8

  @'
set -euo pipefail
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
pytest -q
'@ | Set-Content -LiteralPath (Join-Path $off "run-tests.sh") -Encoding UTF8
}

Write-Host "`n✅ Wheelhouse organized and verified in '$Dist'"
if ($WriteOfflineScripts) {
  Write-Host "   Offline helpers written to scripts/offline/"
}
