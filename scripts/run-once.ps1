$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".env")) {
  throw ".env not found. Run scripts\enroll-local.ps1 first."
}

docker compose run --rm processor python -m processor.main once
