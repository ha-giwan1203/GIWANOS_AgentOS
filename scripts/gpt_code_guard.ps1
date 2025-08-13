# VELOS 운영 철학 선언문: 파일명 고정, 하드코딩 금지, 실행 전 이중검증, 실패는 기록 후 차단
param(
  [string]$Root = $(if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { "C:\giwanos" }),
  [string]$CodePath = "$($env:VELOS_CODE_PATH)",
  [string]$ReportPath = "$Root\data\reports\guard_report_$(Get-Date -f yyyyMMdd_HHmmss).json"
)

$ErrorActionPreference = "Stop"
Set-Location $Root
function W($m){ Write-Host "=== $m ===" }

try {
  if (-not (Test-Path $Root)) { throw "Root not found: $Root" }
  if (-not $CodePath) { throw "VELOS_CODE_PATH not set" }
  if (-not (Test-Path $CodePath)) { throw "CodePath not found: $CodePath" }

  $override = [bool]($env:VELOS_GUARD_OVERRIDE)
  $manifest = "C:\giwanos\configs\security\guard_hashes.json"
  if (-not $override) {
    if (-not (Test-Path $manifest)) { throw "hash manifest missing: $manifest (set VELOS_GUARD_OVERRIDE=1 to bypass)" }
    $m = Get-Content $manifest -Raw | ConvertFrom-Json
    foreach ($f in $m.files) {
      if (-not (Test-Path $f.path)) { throw "guard file missing: $($f.path)" }
      $hash = (Get-FileHash -LiteralPath $f.path -Algorithm SHA256).Hash.ToLower()
      if ($hash -ne $f.sha256.ToLower()) { throw "hash mismatch: $($f.path)" }
    }
  } else {
    Write-Warning "OVERRIDE MODE: hash check bypassed"
  }

  W "[install]"
  python -m pip install --upgrade pip | Out-Null
  if (Test-Path "$Root\requirements.txt") { python -m pip install -r "$Root\requirements.txt" | Out-Null }

  W "[lint]";   python -m ruff check "$CodePath"
  W "[format]"; python -m ruff format "$CodePath"
  W "[security]"; bandit -r "$CodePath" -x "venv,C:\Users\User\venvs"
  W "[type]";   python -m mypy "$CodePath"

  $cov = "no-tests"
  if (Test-Path "$Root\tests") {
    W "[tests]"
    coverage run -m pytest -q
    $cov = coverage report -m
  }

  if (Test-Path "$Root\requirements.txt") {
    W "[audit]"
    pip-audit -r "$Root\requirements.txt" | Out-Null
  }

  New-Item -ItemType Directory -Force -Path "$Root\data\reports" | Out-Null
  @{
    ok = $true; root = $Root; codePath = $CodePath; override = $override; coverage = $cov
    timestamp = (Get-Date).ToString("o"); summary = "검사 통과"
  } | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $ReportPath
  Write-Host "PASS :: $ReportPath"

} catch {
  $msg = $_.ToString()
  New-Item -ItemType Directory -Force -Path "$Root\data\reports" | Out-Null
  @{
    ok = $false; error = $msg; root = $Root; codePath = $CodePath; override = [bool]($env:VELOS_GUARD_OVERRIDE)
    timestamp = (Get-Date).ToString("o"); summary = "검사 실패"
  } | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $ReportPath
  Write-Error "FAIL :: $ReportPath"; exit 1
}


