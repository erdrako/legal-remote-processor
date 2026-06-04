param(
  [int]$Tier = 0,
  [switch]$InstallDependencies,
  [switch]$EnableOllama,
  [switch]$SkipImageBuild,
  [string]$ImageName = "lexmapa/legal-remote-processor:local-ocr"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\setup.ps1" `
  -Tier $Tier `
  -InstallDependencies:$InstallDependencies `
  -EnableOllama:$EnableOllama `
  -SkipImageBuild:$SkipImageBuild `
  -ImageName $ImageName
