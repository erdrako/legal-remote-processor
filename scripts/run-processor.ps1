$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".env")) {
  throw ".env not found. Run scripts\enroll-local.ps1 first."
}

docker compose up -d processor
Write-Host "Processor started. Use scripts\doctor.ps1 or https://lexmapa.linqorait.com/ops to inspect status."
