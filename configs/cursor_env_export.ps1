# VELOS 운영 철학 선언문
param([string]$EnvPath, [switch]$Copy)
$ErrorActionPreference = "Stop"

Import-Module (Join-Path (Get-Location) "tools\velos.common.psm1") -Force
if (-not $EnvPath) { $EnvPath = (Join-Path (Get-VelosRoot) ".env") }

if (-not (Test-Path $EnvPath)) { Write-Error ".env not found: $EnvPath"; exit 1 }
$content = Get-Content -Raw -LiteralPath $EnvPath
$keyLine = ($content -split "`r?`n") | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' }
if (-not $keyLine) { Write-Host "OPENAI_API_KEY not found in $EnvPath"; exit 2 }

$val = $keyLine -replace '^\s*OPENAI_API_KEY\s*=\s*', ''
$masked = ($val -replace '^(.{6}).*(.{4})$', '$1********$2')
Write-Host "OPENAI_API_KEY (masked): $masked"
if ($Copy) { Set-Clipboard -Value $val; Write-Host "Key copied. Paste in Cursor → Settings → API Keys." }