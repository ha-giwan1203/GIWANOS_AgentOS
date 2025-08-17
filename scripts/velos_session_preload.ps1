# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

$ErrorActionPreference = "Stop"
$ROOT = "C:\giwanos"
$PY = Join-Path $ROOT ".venv_link\Scripts\python.exe"

Write-Host "[VELOS] Session Preload Starting..." -ForegroundColor Green

# 1. 핫버퍼 미리 생성
Write-Host "1. Preloading hot buffer..." -ForegroundColor Yellow
& $PY "$ROOT\scripts\preload_hotbuf.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Hot buffer preload failed" -ForegroundColor Yellow
}
else {
    Write-Host "   ✅ Hot buffer ready" -ForegroundColor Green
}

# 2. 세션 메모리 부트스트랩
Write-Host "2. Bootstrapping session memory..." -ForegroundColor Yellow
& $PY "$ROOT\scripts\bootstrap_hotbuf.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Session bootstrap failed" -ForegroundColor Yellow
}
else {
    Write-Host "   ✅ Session memory ready" -ForegroundColor Green
}

# 3. 정책 강제 시스템 테스트
Write-Host "3. Testing policy enforcement..." -ForegroundColor Yellow
& $PY "$ROOT\scripts\test_velos_integration.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Policy enforcement test failed" -ForegroundColor Yellow
}
else {
    Write-Host "   ✅ Policy enforcement ready" -ForegroundColor Green
}

Write-Host "[VELOS] ✅ Session preload completed" -ForegroundColor Green
exit 0
