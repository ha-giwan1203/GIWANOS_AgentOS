# VELOS 운영 철학 선언문
[CmdletBinding()]
param(
  [string]$EnvPath,
  [switch]$Copy
)

$ErrorActionPreference = "Stop"

# 기본 경로 우선순위:
# 1) -EnvPath 인자
# 2) 환경변수 VELOS_ENV_PATH
# 3) C:\giwanos\configs\.env
# 4) C:\giwanos\.env
function Get-VelosRoot {
  $root = $env:VELOS_ROOT; if (-not $root) { $root = "C:\giwanos" }
  [IO.Path]::GetFullPath($root)
}

if (-not $EnvPath -or [string]::IsNullOrWhiteSpace($EnvPath)) {
  if ($env:VELOS_ENV_PATH) {
    $EnvPath = $env:VELOS_ENV_PATH
  } else {
    $root = Get-VelosRoot
    $cand1 = Join-Path $root "configs\.env"
    $cand2 = Join-Path $root ".env"
    $EnvPath = $(if (Test-Path $cand1) { $cand1 } else { $cand2 })
  }
}

if (-not (Test-Path $EnvPath)) {
  Write-Error ".env not found: $EnvPath"
  exit 1
}

# .env에서 OPENAI_API_KEY 라인 파싱
$content = Get-Content -Raw -LiteralPath $EnvPath
$keyLine = ($content -split "`r?`n") | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' }
if (-not $keyLine) { Write-Host "OPENAI_API_KEY not found in $EnvPath"; exit 2 }

$val = $keyLine -replace '^\s*OPENAI_API_KEY\s*=\s*', ''
$masked = ($val -replace '^(.{6}).*(.{4})$', '$1********$2')

Write-Host ("[cursor_env_export] source={0}" -f $EnvPath)
Write-Host ("[cursor_env_export] OPENAI_API_KEY(masked)={0}" -f $masked)

if ($Copy) {
  Set-Clipboard -Value $val
  Write-Host "[cursor_env_export] Copied to clipboard. Paste into Cursor → Settings → API Keys."
}