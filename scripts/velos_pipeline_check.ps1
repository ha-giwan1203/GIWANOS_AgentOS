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
param(
  [string]$Room="roomA",
  [string]$User="local"
)
$ErrorActionPreference="Stop"
$py="$(if ($env:VELOS_PYTHON) { $env:VELOS_PYTHON } else { "python" })"

# 0. 브리지 헬스
& $py $(Join-Path (Join-Path $env:VELOS_ROOT "scripts") "velos_bridge.py") --probe | Out-Null

# 1. 테스트 메시지 투입
$idem="smoke-"+(Get-Date -f yyyyMMddHHmmss)
$env:VELOS_ALLOW_BRIDGE="1"
& $py $(Join-Path (Join-Path $env:VELOS_ROOT "scripts") "velos_bridge.py") --ingest "pipeline_smoke_$([guid]::NewGuid())" --idempotency $idem --room $Room --user $User
$env:VELOS_ALLOW_BRIDGE=$null

# 2. 스케줄 플러시 1회(태스크 실패시 수동 플러시로 폴백)
try { schtasks /run /tn "VELOS Bridge Flush" 2>$null; Start-Sleep 3 } catch { & $py $(Join-Path (Join-Path $env:VELOS_ROOT "scripts") "velos_bridge.py") }

# 3. 마스터 루프 프리체크/드라이런
& $py $(Join-Path (Join-Path $env:VELOS_ROOT "scripts") "run_giwanos_master_loop.py") --precheck
& $py $(Join-Path (Join-Path $env:VELOS_ROOT "scripts") "run_giwanos_master_loop.py") --dry-run

# 4. 멱등키 반영 확인
& $py -c "import sqlite3;con=sqlite3.connect(r'$(Join-Path (Join-Path $env:VELOS_ROOT "data") "velos.db")');print('IDEMP_COUNT=',con.execute('select count(*) from messages where idempotency_key=?',(r'$idem',)).fetchone()[0]);con.close()"
Write-Host "`n[HEALTH]" -ForegroundColor Cyan
Get-Content $(Join-Path (Join-Path $env:VELOS_ROOT "data\\logs") "system_health.json") -Raw | Write-Output
