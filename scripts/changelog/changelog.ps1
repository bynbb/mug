$ErrorActionPreference = "Stop"

# Resolve repo root from this script's folder: scripts/changelog/
$RepoRoot      = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$ChangelogDir  = Join-Path $RepoRoot 'docs'
$ChangelogFile = Join-Path $ChangelogDir 'CHANGELOG.md'
$ConfigPath    = Join-Path $RepoRoot 'config\node\conventional-changelogrc.js'

# Ensure docs/ exists so -i can write in-place
if (-not (Test-Path $ChangelogDir)) {
  New-Item -ItemType Directory -Path $ChangelogDir | Out-Null
}

npx --no-install conventional-changelog `
  -i "$ChangelogFile" -s `
  --config "$ConfigPath" `
  --no-link-compare

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
