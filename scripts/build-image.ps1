param(
  [string]$ImageName = "lexmapa/legal-remote-processor:local-ocr",
  [switch]$InstallOcr,
  [switch]$NoOcr
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$installOcrValue = if ($NoOcr) { "false" } else { "true" }
docker build --build-arg INSTALL_OCR=$installOcrValue -t $ImageName .
