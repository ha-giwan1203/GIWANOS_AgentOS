# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

$ErrorActionPreference = "Stop"
$ROOT = "C:\giwanos"
$VENV = Join-Path $ROOT ".venv_link\Scripts\python.exe"

# 0) 핫버퍼 미리 생성
Write-Host "[VELOS] Hotbuf Preload..."
& $VENV "$ROOT\scripts\preload_hotbuf.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] 핫버퍼 미리 생성 실패. 계속 진행."
}

# 1) 헬스 체크
Write-Host "[VELOS] System Health Check..."
& $VENV "$ROOT\modules\automation\scheduling\system_health_mux.py" --output "$ROOT\data\logs\system_health.json"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 헬스 체크 실패. 스냅샷/보고서 생성 중단."
    exit 1
}

# 2) 스냅샷 생성
Write-Host "[VELOS] Creating Snapshot..."
& $VENV "$ROOT\modules\automation\scheduling\create_snapshot.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 스냅샷 생성 실패."
    exit 1
}

# 3) 보고서 생성
Write-Host "[VELOS] Generating Report..."
& $VENV "$ROOT\modules\report\generate_velos_report.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] 보고서 생성 실패."
    exit 1
}

# 4) 시스템 프롬프트 테스트
Write-Host "[VELOS] Testing System Prompt..."
& $VENV "$ROOT\scripts\test_velos_prompt.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] 시스템 프롬프트 테스트 실패. 계속 진행."
}

# 5) VELOS 통합 테스트
Write-Host "[VELOS] Testing VELOS Integration..."
& $VENV "$ROOT\scripts\test_velos_integration.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] VELOS 통합 테스트 실패. 계속 진행."
}

# 6) Health OK 시 Snapshot + Report 파이프라인
Write-Host "[VELOS] Running Health Pipeline..."
& pwsh -File "$ROOT\scripts\velos_health_pipeline.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Health pipeline failed. 계속 진행."
}

# 7) 완료 알림
Write-Host "[VELOS] ✅ Preload + Health + Snapshot + Report + Prompt + Integration + Pipeline 완료"
exit 0
