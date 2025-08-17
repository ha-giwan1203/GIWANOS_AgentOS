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
  [string]$Root = "C:\giwanos",
  [string]$TaskName = "VELOS Master Loop"
)

$ErrorActionPreference = "Stop"

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Good($m){ Write-Host "✅ $m" -ForegroundColor Green }
function Warn($m){ Write-Host "⚠️  $m" -ForegroundColor Yellow }
function Bad($m){  Write-Host "❌ $m" -ForegroundColor Red }

# 경로 설정
$Venv = Join-Path $Root ".venv_link"
$Py = Join-Path $Venv "Scripts\python.exe"
$MasterLoopScript = Join-Path $Root "scripts\run_giwanos_master_loop.py"

Write-Host "=== VELOS 마스터 루프 태스크 생성 ===" -ForegroundColor Magenta

# 1. 기존 태스크 확인 및 삭제
Info "1. 기존 태스크 확인..."
$existing_task = schtasks /query /tn $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
  Warn "기존 태스크 발견: $TaskName"
  Info "기존 태스크 삭제 중..."
  schtasks /delete /tn $TaskName /f 2>$null
  if ($LASTEXITCODE -eq 0) {
    Good "기존 태스크 삭제 완료"
  } else {
    Bad "기존 태스크 삭제 실패"
  }
} else {
  Info "기존 태스크 없음"
}

# 2. 스크립트 파일 확인
Info "2. 마스터 루프 스크립트 확인..."
if (Test-Path $MasterLoopScript) {
  Good "마스터 루프 스크립트 존재: $MasterLoopScript"
} else {
  Bad "마스터 루프 스크립트 없음: $MasterLoopScript"
  exit 1
}

# 3. Python 실행 파일 확인
Info "3. Python 실행 파일 확인..."
if (Test-Path $Py) {
  Good "Python 실행 파일 존재: $Py"
} else {
  Bad "Python 실행 파일 없음: $Py"
  exit 1
}

# 4. 태스크 명령 구성
$task_command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"& '$Py' '$MasterLoopScript'`""

Info "4. 태스크 명령 구성..."
Write-Host "   명령: $task_command" -ForegroundColor Gray

# 5. 스케줄 태스크 생성
Info "5. 스케줄 태스크 생성..."
Write-Host "   태스크명: $TaskName" -ForegroundColor Gray
Write-Host "   스케줄: 매일 07:00" -ForegroundColor Gray

schtasks /create /tn $TaskName /sc daily /st 07:00 `
  /tr $task_command `
  /f

if ($LASTEXITCODE -eq 0) {
  Good "VELOS 마스터 루프 태스크 생성 완료"
} else {
  Bad "VELOS 마스터 루프 태스크 생성 실패"
  exit 1
}

# 6. 생성된 태스크 확인
Info "6. 생성된 태스크 확인..."
$task_info = schtasks /query /tn $TaskName /fo csv 2>$null
if ($LASTEXITCODE -eq 0) {
  $task_data = $task_info | ConvertFrom-Csv
  $next_run = $task_data."Next Run Time"
  $status = $task_data."Status"

  Good "태스크 생성 확인 완료"
  Write-Host "   다음 실행: $next_run" -ForegroundColor Cyan
  Write-Host "   상태: $status" -ForegroundColor Cyan
} else {
  Bad "태스크 확인 실패"
  exit 1
}

# 7. 태스크 테스트 실행
Info "7. 태스크 테스트 실행..."
Write-Host "   테스트 명령 실행 중..." -ForegroundColor Gray
$test_result = & $Py $MasterLoopScript 2>&1
$test_exit_code = $LASTEXITCODE

if ($test_exit_code -eq 0) {
  Good "태스크 테스트 성공"
} else {
  Warn "태스크 테스트 실패 (종료 코드: $test_exit_code)"
  Write-Host "   테스트 출력:" -ForegroundColor Gray
  $test_result | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
}

# 8. 헬스 로그 업데이트
Info "8. 헬스 로그 업데이트..."
$health_file = Join-Path $Root "data\logs\system_health.json"

function Read-Json($p){
  try {
    Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
  } catch {
    $null
  }
}

function Write-Json($p,$obj){
  New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($p)) | Out-Null
  $tmp = "$p.tmp"
  ($obj | ConvertTo-Json -Depth 8) | Out-File $tmp -Encoding utf8
  Move-Item $tmp $p -Force
}

$health = Read-Json $health_file
if (-not $health) { $health = @{} }

$health.master_loop_task = @{
  created_ts = [int][double]::Parse((Get-Date -UFormat %s))
  task_name = $TaskName
  command = $task_command
  next_run = $next_run
  status = $status
  test_exit_code = $test_exit_code
  test_ok = ($test_exit_code -eq 0)
}

Write-Json $health_file $health
Good "헬스 로그 업데이트 완료"

# 9. 결과 요약
Write-Host ""
Write-Host "=== VELOS 마스터 루프 태스크 생성 완료 ===" -ForegroundColor Magenta
Good "태스크명: $TaskName"
Good "스케줄: 매일 07:00"
Good "다음 실행: $next_run"
Good "상태: $status"
if ($test_exit_code -eq 0) {
  Good "테스트: 성공"
} else {
  Warn "테스트: 실패 (종료 코드: $test_exit_code)"
}

Write-Host ""
Write-Host "=== 태스크 관리 명령어 ===" -ForegroundColor Cyan
Write-Host "태스크 확인: schtasks /query /tn `"$TaskName`"" -ForegroundColor Gray
Write-Host "태스크 실행: schtasks /run /tn `"$TaskName`"" -ForegroundColor Gray
Write-Host "태스크 삭제: schtasks /delete /tn `"$TaskName`" /f" -ForegroundColor Gray

Good "VELOS 마스터 루프 태스크 생성 완료!"
exit 0
