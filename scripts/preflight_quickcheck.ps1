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
$ErrorActionPreference="Stop"
$ROOT = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { "/workspace" }
$LOG = "$ROOT/data/logs/preflight_{0}.log" -f (Get-Date -Format yyyyMMdd)
function Log($m){ "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"),$m | Out-File -FilePath $LOG -Append -Encoding UTF8 }
# python 존재 확인
if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) { 
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { 
        Log "no python"; exit 1 
    }
}
# 빠른 문법 체크
Get-ChildItem "$ROOT" -Recurse -Filter *.py | ?{ $_.FullName -notmatch '/venv/' } | %{
  & python3 -m py_compile $_.FullName 2>$null
  if ($LASTEXITCODE -ne 0){ Log "py_compile fail: $($_.FullName)"; exit 1 }
}
# 필수 임포트
$pythonCode = @"
import importlib
for m in ["modules.velos_common","modules.report_paths"]:
    importlib.import_module(m)
print("OK")
"@

$pythonCode | python3
if ($LASTEXITCODE -ne 0){ Log "import check failed"; exit 1 }
Log "preflight pass"
