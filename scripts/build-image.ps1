param(
  [switch]$InstallOcr
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root
$installOcrValue = if ($InstallOcr) { "true" } else { "false" }
docker build --build-arg INSTALL_OCR=$installOcrValue -t lexmapa-remote-processor:local .
