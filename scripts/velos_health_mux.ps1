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
# === VELOS System Health MUX (기존 헬스 점검 + Context/Flush 가드) ===
$ErrorActionPreference = "Stop"
$ROOT = "C:\giwanos"
$PY = Join-Path $ROOT ".venv_link\Scripts\python.exe"

# 1) 기존 헬스/무결성 점검 (이미 있는 표준 루틴 재사용)
& $PY "$ROOT\scripts\system_integrity_check.py"
$system_exit = $LASTEXITCODE

& $PY "$ROOT\scripts\data_integrity_check.py"
$data_exit = $LASTEXITCODE

# 2) 컨텍스트/플러시 가드 (시간 초과 시 비명 지르기)
& $PY "$ROOT\scripts\context_guard.py"
$context_exit = $LASTEXITCODE

# 3) 종료코드 전파 (가장 심각한 오류 코드 반환)
$max_exit = [Math]::Max([Math]::Max($system_exit, $data_exit), $context_exit)
exit $max_exit
