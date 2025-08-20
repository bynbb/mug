<# scripts/package.ps1
    Orchestrates: build/vendor organization + offline helpers -> zip.
    Passes -IncludeLinuxWheels through to build-and-vendor.ps1.
#>

[CmdletBinding()]
param(
    [string] $Ref = "",
    [string] $ZipName = "",
    [string] $RuntimeRequirements = "",  # optional: requirements file to download wheels
    [switch] $IncludeLinuxWheels         # also fetch manylinux wheels when downloading
)

# Remove any obk==X.Y.Z pin from requirements before calling build-and-vendor
if (Test-Path $RuntimeRequirements) {
    $reqs = Get-Content $RuntimeRequirements | Where-Object { $_ -notmatch '^obk==' }
    Set-Content $RuntimeRequirements $reqs
}

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (git rev-parse --show-toplevel)

# Organize + verify + (optional) download + write helpers
$bvArgs = @("--WriteOfflineScripts")
if ($RuntimeRequirements) { $bvArgs += @("--RuntimeRequirements", $RuntimeRequirements) }
if ($IncludeLinuxWheels) { $bvArgs += "--IncludeLinuxWheels" }

pwsh -File "$here/build-and-vendor.ps1" @bvArgs

# --- Ensure our own obk wheel is in dist/ (we removed obk from requirements) ---
if (-not (Test-Path "dist")) { New-Item -ItemType Directory -Path "dist" | Out-Null }

# Prefer 'python -m build'; fall back to 'pip wheel .' if 'build' isn't installed
$built = $false
if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m build --wheel --outdir dist 2>$null
    if ($LASTEXITCODE -eq 0) { $built = $true }
}
if (-not $built) {
    pip wheel . -w dist --no-deps
    if ($LASTEXITCODE) { throw "Building local obk wheel failed." }
}

# Zip (reuse your existing make-zip.ps1)
$zipArgs = @()
if ($Ref) { $zipArgs += @("--Ref", $Ref) }
if ($ZipName) { $zipArgs += @("--ZipName", $ZipName) }
pwsh -File "$here/make-zip.ps1" @zipArgs
