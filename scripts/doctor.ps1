$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

Write-Host "Docker:"
try { docker --version } catch { Write-Host "Docker not found" }

Write-Host "Ollama:"
try { ollama --version } catch { Write-Host "Ollama not found; deterministic mode can still run." }

$env:PYTHONPATH = Join-Path $Root "src"
python -m processor.main doctor

if (Test-Path ".env") {
  Write-Host ".env exists."
} else {
  Write-Host ".env missing. Copy .env.example or run scripts\enroll-local.ps1."
}

try {
  docker compose ps
} catch {
  Write-Host "Docker compose status unavailable."
}
