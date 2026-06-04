param(
  [int]$Tier = 0,
  [switch]$InstallDependencies,
  [switch]$EnableOllama,
  [switch]$SkipImageBuild,
  [string]$ImageName = "lexmapa/legal-remote-processor:local-ocr",
  [int]$DockerStartTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Get-RamGb {
  try {
    return [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
  } catch {
    return 0
  }
}

function Get-SystemProfile {
  $drive = Get-Item $Root
  $disk = Get-PSDrive -Name $drive.PSDrive.Name
  return [pscustomobject]@{
    Architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
    CpuCount = [Environment]::ProcessorCount
    RamGb = Get-RamGb
    FreeDiskGb = [math]::Round($disk.Free / 1GB, 2)
  }
}

function Get-ProcessorTier([double]$RamGb, [double]$FreeDiskGb, [int]$CpuCount) {
  if ($RamGb -ge 64 -and $CpuCount -ge 12 -and $FreeDiskGb -ge 120) { return 5 }
  if ($RamGb -ge 32 -and $CpuCount -ge 8 -and $FreeDiskGb -ge 80) { return 4 }
  if ($RamGb -ge 16 -and $CpuCount -ge 6 -and $FreeDiskGb -ge 50) { return 3 }
  if ($RamGb -ge 12 -and $CpuCount -ge 4 -and $FreeDiskGb -ge 30) { return 2 }
  return 1
}

function Assert-MinimumHardware($Profile) {
  $reasons = @()
  if ($Profile.Architecture -notmatch "X64|Arm64") {
    $reasons += "CPU 64-bit requerida."
  }
  if ($Profile.RamGb -lt 8) {
    $reasons += "RAM insuficiente: se requieren al menos 8 GB."
  }
  if ($Profile.FreeDiskGb -lt 20) {
    $reasons += "Disco libre insuficiente: se requieren al menos 20 GB."
  }
  if ($reasons.Count -gt 0) {
    $reasons | ForEach-Object { Write-Host "- $_" }
    throw "Esta PC no soporta el tier minimo. No se instalo ni configuro nada."
  }
}

function Set-EnvValue([string]$Path, [string]$Key, [string]$Value) {
  $lines = if (Test-Path $Path) { @(Get-Content -LiteralPath $Path) } else { @() }
  $found = $false
  $updated = foreach ($line in $lines) {
    if ($line -match "^$([regex]::Escape($Key))=") {
      $found = $true
      "$Key=$Value"
    } else {
      $line
    }
  }
  if (-not $found) {
    $updated += "$Key=$Value"
  }
  Set-Content -LiteralPath $Path -Value $updated -Encoding utf8
}

function Install-WithWinget([string]$PackageId, [string]$Name) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget es requerido para instalar $Name automaticamente."
  }
  winget install -e --id $PackageId --accept-package-agreements --accept-source-agreements
}

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

Write-Host "LexMapa Remote Processor setup"
Write-Host "Validando hardware minimo..."
$profile = Get-SystemProfile
Assert-MinimumHardware $profile

$detectedTier = Get-ProcessorTier $profile.RamGb $profile.FreeDiskGb $profile.CpuCount
$selectedTier = if ($Tier -gt 0) { $Tier } else { $detectedTier }
if ($selectedTier -gt $detectedTier) {
  throw "El tier solicitado ($selectedTier) supera el tier seguro detectado ($detectedTier)."
}

Write-Host "Tier detectado: $detectedTier. Tier configurado: $selectedTier."

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Archivo .env creado desde .env.example."
}

Set-EnvValue ".env" "LEXMAPA_PROCESSOR_TIER" "$selectedTier"
Set-EnvValue ".env" "LEXMAPA_PROCESSOR_IMAGE" "$ImageName"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  if (-not $InstallDependencies) {
    throw "Docker no esta instalado. Ejecuta este script con -InstallDependencies para instalar Docker Desktop."
  }
  Install-WithWinget "Docker.DockerDesktop" "Docker Desktop"
}

if ($EnableOllama -and -not (Get-Command ollama -ErrorAction SilentlyContinue)) {
  if (-not $InstallDependencies) {
    throw "Ollama no esta instalado. Ejecuta este script con -InstallDependencies -EnableOllama para instalarlo."
  }
  Install-WithWinget "Ollama.Ollama" "Ollama"
  Set-EnvValue ".env" "PROCESSOR_ENABLE_OLLAMA" "true"
} elseif ($EnableOllama) {
  Set-EnvValue ".env" "PROCESSOR_ENABLE_OLLAMA" "true"
}

Wait-Docker $DockerStartTimeoutSeconds

if (-not $SkipImageBuild) {
  & "$PSScriptRoot\build-image.ps1" -ImageName $ImageName -InstallOcr
}

Write-Host "Setup inicial completo."
Write-Host "Siguiente paso: enrolar el procesador si .env no tiene credenciales."
Write-Host "Luego ejecutar: .\scripts\run.ps1"
