# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
[CmdletBinding()]
param(
  [switch]$NoOpen,     # postrun에서 Cursor 열기 생략
  [switch]$NoPush,     # postrun에서 git push 생략
  [switch]$VerbosePy   # 파이썬 루프를 --verbose로
)

# ==== VELOS env loader (auto venv select) ====
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$ENVFILE = Join-Path $ROOT "configs\.env"

# 1) .env 로드
if (Test-Path $ENVFILE) {
  foreach ($line in Get-Content $ENVFILE) {
    if ($line -match '^\s*#') { continue }
    if ($line -match '^\s*(\w+)\s*=\s*(.+)\s*$') { Set-Item -Path "env:$($matches[1])" -Value $matches[2] }
  }
}

# 2) venv 경로 결정: .venv_link > .venv > (옵션) VENV_PATH > system
$venvCandidates = @(
  ".venv_link\Scripts\python.exe",
  ".venv\Scripts\python.exe"
)
if ($env:VENV_PATH) { $venvCandidates = @("$($env:VENV_PATH)\python.exe") + $venvCandidates }

$py = $null
foreach ($cand in $venvCandidates) {
  $p = Join-Path $ROOT $cand
  if (Test-Path $p) { $py = $p; break }
}
if (-not $py) { $py = "python"; Write-Warning "[run-all] venv not found. system python 사용" }
else { Write-Host   "[run-all] using venv python: $py" -ForegroundColor Green }

# 3) Git 한글 안전 설정(무해하니 매번 시도)
git config --global core.quotepath false 2>$null
git config --global i18n.logOutputEncoding utf-8 2>$null
git config --global i18n.commitEncoding utf-8 2>$null
# ==== END VELOS env loader ====

$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$ROOT = [IO.Path]::GetFullPath($ROOT)
Set-Location $ROOT

function Info($m) { Write-Host "[run-all] $m" }
function Warn($m) { Write-Host "[run-all][WARN] $m" -ForegroundColor Yellow }

# 1) 마스터 루프 실행(파이썬 or 기존 ps1 중 가용한 쪽)
$loopPy = Join-Path $ROOT "scripts\run_giwanos_master_loop.py"
$loopPs = Join-Path $ROOT "tools\velos-run.ps1"

if (Test-Path $loopPy) {
  $args = @()
  if ($VerbosePy) { $args += "--verbose" }
  Info "run python loop..."

  & $py $loopPy @args
  $code = $LASTEXITCODE
}
elseif (Test-Path $loopPs) {
  Info "run velos-run.ps1 -Once..."
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $loopPs -Once
  $code = $LASTEXITCODE
}
else {
  throw "마스터 루프 엔트리 없음: $loopPy / $loopPs"
}

if ($code -ne 0) {
  Warn ("master loop exited with code {0}" -f $code)
}

# 2) postrun 호출(리포트 찾기 + git push + Cursor 열기)
$post = Join-Path $ROOT "tools\velos-postrun.ps1"
if (-not (Test-Path $post)) { throw "postrun 스크립트 없음: $post" }

$prArgs = @()
if ($NoOpen) { $prArgs += "-NoOpen" }
if ($NoPush) { $prArgs += "-NoPush" }

Info "postrun..."
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $post @prArgs
Info "done."
