param(
  [switch]$Rebuild,
  [switch]$NoOcr,
  [string]$ImageName = "lexmapa/legal-remote-processor:local-ocr"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\run.ps1" `
  -Once `
  -Rebuild:$Rebuild `
  -NoOcr:$NoOcr `
  -ImageName $ImageName
