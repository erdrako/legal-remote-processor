param(
  [switch]$Once,
  [switch]$Continuous,
  [switch]$Rebuild,
  [switch]$NoOcr,
  [string]$ImageName = "lexmapa/legal-remote-processor:local-ocr",
  [int]$DockerStartTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Test-DockerRunning {
  try {
    docker info *> $null
    return $true
  } catch {
    return $false
  }
}

function Start-DockerDesktopIfPossible {
  $paths = @(
    (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
    (Join-Path $env:LocalAppData "Docker\Docker Desktop\Docker Desktop.exe"),
    (Join-Path $env:LocalAppData "Docker\Docker\Docker Desktop.exe")
  )
  $dockerDesktop = $paths | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($dockerDesktop) {
    Write-Host "Docker no esta levantado. Iniciando Docker Desktop..."
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
  }
}

function Wait-Docker([int]$TimeoutSeconds) {
  if (Test-DockerRunning) { return }
  Start-DockerDesktopIfPossible

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    if (Test-DockerRunning) { return }
  }
  throw "Docker esta instalado pero no respondio dentro de $TimeoutSeconds segundos."
}

function Test-DockerImage([string]$Name) {
  try {
    docker image inspect $Name *> $null
    return $true
  } catch {
    return $false
  }
}

function Remove-ProcessorServiceContainer {
  try {
    docker compose rm --stop --force processor *> $null
  } catch {
    # No existing service container is a normal state for drain/once runs.
  }
}

if (-not (Test-Path ".env")) {
  throw ".env no existe. Ejecuta .\scripts\setup.ps1 y luego enrola el procesador."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "Docker no esta instalado. Ejecuta .\scripts\setup.ps1 -InstallDependencies."
}

Wait-Docker $DockerStartTimeoutSeconds

if ($Rebuild -or -not (Test-DockerImage $ImageName)) {
  Write-Host "Imagen $ImageName no encontrada o rebuild solicitado. Construyendo..."
  if ($NoOcr) {
    & "$PSScriptRoot\build-image.ps1" -ImageName $ImageName -NoOcr
  } else {
    & "$PSScriptRoot\build-image.ps1" -ImageName $ImageName -InstallOcr
  }
}

$env:LEXMAPA_PROCESSOR_IMAGE = $ImageName
$env:INSTALL_OCR = if ($NoOcr) { "false" } else { "true" }

if ($Once) {
  Remove-ProcessorServiceContainer
  docker compose run --rm processor python -m processor.main once
} elseif ($Continuous) {
  docker compose up -d processor
  Write-Host "Procesador continuo iniciado con imagen $ImageName."
  Write-Host "Estado operativo: https://lexmapa.linqorait.com/ops"
} else {
  Remove-ProcessorServiceContainer
  docker compose run --rm processor python -m processor.main drain
}
