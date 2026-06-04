param(
  [int]$Tier = 0,
  [switch]$InstallDependencies,
  [switch]$EnableOllama
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "Running LexMapa remote processor preflight..."
$env:PYTHONPATH = Join-Path $Root "src"
$preflightJson = python -m processor.main preflight 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host $preflightJson
  throw "Preflight failed. No dependencies were installed."
}

$preflight = $preflightJson | ConvertFrom-Json
if (-not $preflight.can_install) {
  $preflight | ConvertTo-Json -Depth 6
  throw "This PC does not support the minimum tier. No dependencies were installed."
}

$selectedTier = if ($Tier -gt 0) { $Tier } else { [int]$preflight.tier }
if ($selectedTier -gt [int]$preflight.tier) {
  throw "Requested tier $selectedTier is higher than detected safe tier $($preflight.tier)."
}

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  (Get-Content ".env") -replace "LEXMAPA_PROCESSOR_TIER=1", "LEXMAPA_PROCESSOR_TIER=$selectedTier" | Set-Content ".env"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  if (-not $InstallDependencies) {
    throw "Docker is missing. Re-run with -InstallDependencies after reviewing docs/INSTALL.md."
  }
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget is required for automatic Docker installation on Windows."
  }
  winget install -e --id Docker.DockerDesktop
}

if ($EnableOllama -and -not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  if (-not $InstallDependencies) {
    throw "Ollama is missing. Re-run with -InstallDependencies -EnableOllama after reviewing docs/INSTALL.md."
  }
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget is required for automatic Ollama installation on Windows."
  }
  winget install -e --id Ollama.Ollama
}

& "$PSScriptRoot\build-image.ps1"
Write-Host "Bootstrap completed. Next: scripts\enroll-local.ps1, then scripts\run-once.ps1 or scripts\run-processor.ps1."
