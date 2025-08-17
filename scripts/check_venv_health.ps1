# VELOS 운영 철학 선언문: 파일명/경로 불변, 자가 검증 필수, 결과 기록, 거짓 코드 금지.
[CmdletBinding()]
param(
    [string]$Root = "C:\giwanos",
    [string]$VenvRel = ".venv_link",   # 가상환경 폴더명
    [string]$Req = "C:\giwanos\configs\requirements.txt",  # 있으면 패키지 확인에 사용
    [string[]]$ProbePkgs = @("pip", "setuptools", "wheel")   # 최소 프로브 패키지
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues["Out-File:Encoding"] = "utf8"
function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Good($m) { Write-Host "✅ $m" -ForegroundColor Green }
function Warn($m) { Write-Host "⚠️  $m" -ForegroundColor Yellow }
function Bad($m) { Write-Host "❌ $m" -ForegroundColor Red }

# 0) 경로 계산
$Venv = Join-Path $Root $VenvRel
$Bin = Join-Path $Venv "Scripts"
$Py = Join-Path $Bin "python.exe"
$Act = Join-Path $Bin "activate"
$Cfg = Join-Path $Venv "pyvenv.cfg"
$Health = Join-Path $Root "data\logs\system_health.json"
$newline = [Environment]::NewLine

# 내부 헬퍼
function Read-Json($p) { try { Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null } }
function Write-Json($p, $obj) {
    New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($p)) | Out-Null
    $tmp = "$p.tmp"
    ($obj | ConvertTo-Json -Depth 8) | Out-File $tmp -Encoding utf8
    Move-Item $tmp $p -Force
}

# 1) 기본 구조 점검
if (-not (Test-Path $Root)) { Bad "ROOT 경로가 없음: $Root"; exit 2 }
Info "ROOT: $Root"

$score = 0   # 0=정상, 1=경고(수정 가능), 2=망가짐
$notes = @()

if (-not (Test-Path $Venv)) {
    Warn "가상환경 폴더가 없음: $Venv"
    $score = [Math]::Max($score, 2)
    $notes += "venv_missing"
}
else {
    Good "가상환경 폴더 존재"
}

# 2) 실행 파일/활성화 스크립트
if (-not (Test-Path $Py)) { Warn "python.exe 없음: $Py"; $score = [Math]::Max($score, 2); $notes += "python_exe_missing" }
else { Good "python.exe 존재: $Py" }

if (-not (Test-Path $Act)) { Warn "activate 스크립트 없음: $Act"; $score = [Math]::Max($score, 1); $notes += "activate_missing" }
else { Info "activate 스크립트 확인" }

# 3) pyvenv.cfg 무결성
if (-not (Test-Path $Cfg)) { Warn "pyvenv.cfg 없음: $Cfg"; $score = [Math]::Max($score, 1); $notes += "pyvenv_cfg_missing" }
else {
    $cfgText = Get-Content $Cfg -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($cfgText)) { Warn "pyvenv.cfg가 비어있음"; $score = [Math]::Max($score, 2); $notes += "pyvenv_cfg_empty" }
    else { Info "pyvenv.cfg 확인" }
}

# 4) 현재 세션 python이 어디를 가리키는지
$env:PATH = "$Bin;$env:PATH"
$whichPy = & $Py -c "import sys;print(sys.executable)" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($whichPy)) { Bad "가상환경 Python 실행 실패"; $score = [Math]::Max($score, 2); $notes += "python_invoke_failed" }
else { Good "가상환경 Python 실행 OK: $whichPy" }

# 5) 버전/실행체크
$ver = & $Py -c "import sys;print(sys.version)" 2>$null
if ($LASTEXITCODE -eq 0) { Info "Python 버전: $ver" } else { Warn "Python 버전 확인 실패"; $score = [Math]::Max($score, 1) }

# 6) 패키지 최소 프로브
$missing = @()
foreach ($p in $ProbePkgs) {
    $env:PROBE_PKG = $p
    $result = & $Py -c "import sys, importlib, json, os; mod = os.environ.get('PROBE_PKG'); importlib.import_module(mod); print('OK:'+mod)" 2>$null
    if ($LASTEXITCODE -ne 0) { $missing += $p; continue }
}
if ($missing.Count -gt 0) {
    Warn ("필수 최소 패키지 누락: " + ($missing -join ", "))
    $score = [Math]::Max($score, 1)
}
else {
    Good "최소 패키지 로딩 OK"
}

# 7) requirements.txt 기반(선택)
$reqMissing = @()
if (Test-Path $Req) {
    Info "requirements.txt 기반 빠른 존재 확인"
    $reqLines = (Get-Content $Req | Where-Object { $_ -and -not $_.StartsWith('#') })
    $top = $reqLines | Select-Object -First 15
    foreach ($line in $top) {
        $name = ($line -split '[<>=~! ]')[0]
        if (-not $name) { continue }
        $env:CHK_NAME = $name
        $result = & $Py -c "import importlib, os, sys; mod = os.environ.get('CHK_NAME'); importlib.import_module(mod); print('OK:'+mod)" 2>$null
        if ($LASTEXITCODE -ne 0) { $reqMissing += $name }
    }
    if ($reqMissing.Count -gt 0) {
        Warn ("일부 요구 패키지 미로딩(상위 15 스캔): " + ($reqMissing -join ", "))
        $notes += "req_probe_missing"
    }
    else {
        Info "상위 15개 패키지 로딩 OK"
    }
}
else {
    Info "requirements.txt 없음. 이 단계 스킵"
}

# 8) 결과 요약
Write-Host ""
Write-Host "=== VENV HEALTH SUMMARY ===" -ForegroundColor Magenta
switch ($score) {
    0 { Good  "상태: 정상" }
    1 { Warn  "상태: 경고(수정 가능)" }
    2 { Bad   "상태: 손상(재생성 권장)" }
}
Write-Host ("활성 python: {0}" -f $whichPy)
if ($missing.Count -gt 0) { Write-Host ("최소 패키지 누락: {0}" -f ($missing -join ", ")) }
if ($reqMissing.Count -gt 0) { Write-Host ("req 상위 누락: {0}" -f ($reqMissing -join ", ")) }
Write-Host "==========================="

# 9) 헬스 로그 업데이트
$h = Read-Json $Health
if (-not $h) { $h = @{} }
$h.venv_health = @{
    checked_ts  = [int][double]::Parse((Get-Date -UFormat %s))
    root        = $Root
    venv        = $VenvRel
    python      = $whichPy
    status      = $(switch ($score) { 0 { "ok" }1 { "warn" }2 { "broken" } })
    notes       = $notes
    missing_min = $missing
    missing_req = $reqMissing
}
Write-Json $Health $h
Good "헬스 로그 업데이트 완료: $Health"

# 10) 종료 코드(자동화 친화)
if ($score -eq 2) { exit 2 }
elseif ($score -eq 1) { exit 1 }
else { exit 0 }
