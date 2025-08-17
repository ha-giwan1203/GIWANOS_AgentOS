# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

$ErrorActionPreference = "Stop"
$ROOT = "C:\giwanos"
$PY = Join-Path $ROOT ".venv_link\Scripts\python.exe"

# 세션 핫버퍼 미리 생성(없거나 만료 시 자동 재생성)
& $PY "$ROOT\scripts\preload_hotbuf.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 핫버퍼 미리 생성 실패"
    exit 1
}

Write-Host "[VELOS] ✅ 핫버퍼 미리 생성 완료"
exit 0
