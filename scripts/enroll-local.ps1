param(
  [string]$TokenFile = "..\legal-infrastructure\private\remote-processor-tokens.generated.txt"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

$resolvedTokenFile = Resolve-Path $TokenFile
$line = Get-Content -LiteralPath $resolvedTokenFile | Where-Object { $_ -like "PROCESSOR_ENROLLMENT_TOKEN=*" } | Select-Object -First 1
if (-not $line) {
  throw "PROCESSOR_ENROLLMENT_TOKEN was not found in token file."
}
$enrollmentToken = $line -replace "^PROCESSOR_ENROLLMENT_TOKEN=", ""

$apiBase = "https://lexmapa-api.linqorait.com"
$processorSecretResponse = Invoke-RestMethod `
  -Method Post `
  -Uri "$apiBase/processors/enroll" `
  -Headers @{ Authorization = "Bearer $enrollmentToken" } `
  -ContentType "application/json" `
  -Body (@{
    displayName = "Procesador remoto LexMapa local"
    tier = 1
    capabilities = @("PDF_TEXT", "LEGAL_REFERENCES", "AFFECTED_LEGAL_ITEMS", "LEGAL_DIFF_CANDIDATES")
    modelName = "deterministic-no-ollama"
    processorVersion = "0.1.0"
  } | ConvertTo-Json)

$envLines = Get-Content ".env"
$updates = @{
  LEXMAPA_PROCESSOR_ID = $processorSecretResponse.processor.id
  LEXMAPA_PROCESSOR_SECRET = $processorSecretResponse.processorSecret
  LEXMAPA_PROCESSOR_NAME = "Procesador remoto LexMapa local"
  LEXMAPA_PROCESSOR_VERSION = "0.1.0"
  PROCESSOR_ENABLE_OLLAMA = "false"
}

foreach ($key in $updates.Keys) {
  $value = $updates[$key]
  if ($envLines -match "^$key=") {
    $envLines = $envLines -replace "^$key=.*", "$key=$value"
  } else {
    $envLines += "$key=$value"
  }
}

Set-Content ".env" $envLines -Encoding utf8
Write-Host "Processor enrolled and .env updated. Processor id: $($processorSecretResponse.processor.id)"
