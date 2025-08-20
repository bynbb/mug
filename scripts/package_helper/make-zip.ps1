<# Clean archive from Git + include ./dist/ recursively if present #>
param(
  [string]$Ref = "HEAD",
  [string]$ZipName = ""
)

$ErrorActionPreference = "Stop"

function Require-Cmd($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required command not found: $name"
  }
}

Require-Cmd git

# Always operate from repo root
$repoRoot = (& git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

git rev-parse --verify $Ref > $null 2>&1

if ([string]::IsNullOrWhiteSpace($ZipName)) {
  $refSafe = ($Ref -replace '[^A-Za-z0-9._-]', '_')
  $ZipName = $(if ($Ref -eq "HEAD") { "obk_clean.zip" } else { "obk_$refSafe.zip" })
}

Write-Host "📦 Creating base archive from $Ref -> $ZipName"
git archive --format=zip --output "$ZipName" $Ref

function Add-ToZip {
  param([string]$Zip, [string[]]$Paths)
  $Paths = $Paths | Where-Object { Test-Path $_ }
  if (-not $Paths -or $Paths.Count -eq 0) { return }

  $compress = Get-Command Compress-Archive -ErrorAction SilentlyContinue
  if ($compress -and ($compress.Parameters.ContainsKey("Update"))) {
    Write-Host "➕ Adding to zip via Compress-Archive -Update"
    Compress-Archive -Path $Paths -DestinationPath $Zip -Update
    return
  }

  $sevenZ = Get-Command 7z -ErrorAction SilentlyContinue
  if ($sevenZ) {
    Write-Host "➕ Adding to zip via 7-Zip"
    & 7z a "$Zip" $Paths | Out-Null
    return
  }

  throw "Neither Compress-Archive -Update nor 7z is available to update the zip."
}

# Include dist/ recursively if present (build outputs + vendored wheels)
if (Test-Path ".\dist") {
  Write-Host "➕ Including ./dist/ in $ZipName"
  Add-ToZip -Zip $ZipName -Paths ".\dist"
} else {
  Write-Host "ℹ️  No dist/ directory found; skipping."
}

Write-Host "`n✅ Done -> $ZipName"
