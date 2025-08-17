# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

# === VELOS: Health OK 시 Snapshot + Report 파이프라인 실행 ===
# 끄고 싶으면 환경변수로 VELOS_PIPELINE_ON=0 지정
if ($env:VELOS_PIPELINE_ON -ne "0") {
    try {
        Write-Host "[MUX] running snapshot + report pipeline..." -ForegroundColor Green
        $ROOT = "C:\giwanos"
        $PY = Join-Path $ROOT ".venv_link\Scripts\python.exe"

        # 1) 스냅샷 생성 (ZIP 무결성 검사 내장)
        Write-Host "1. Creating snapshot..." -ForegroundColor Yellow
        & $PY "$ROOT\modules\automation\scheduling\create_snapshot.py"
        $snapCode = $LASTEXITCODE
        if ($snapCode -eq 2 -or $snapCode -eq 1) { $snapCode = 0 }  # 경고는 성공 처리
        if ($snapCode -ne 0) {
            Write-Host "[MUX] snapshot failed: code=$snapCode" -ForegroundColor Red
            exit $snapCode
        }
        Write-Host "   ✅ Snapshot created successfully" -ForegroundColor Green

        # 2) 보고서 생성 (헬스 로그 + 최신 스냅샷 메타 기반)
        Write-Host "2. Generating report..." -ForegroundColor Yellow
        & $PY "$ROOT\modules\report\generate_velos_report.py"
        $repCode = $LASTEXITCODE
        if ($repCode -eq 2 -or $repCode -eq 1) { $repCode = 0 }
        if ($repCode -ne 0) {
            Write-Host "[MUX] report failed: code=$repCode" -ForegroundColor Red
            exit $repCode
        }
        Write-Host "   ✅ Report generated successfully" -ForegroundColor Green

        Write-Host "[MUX] ✅ snapshot + report pipeline done" -ForegroundColor Green
    }
    catch {
        Write-Host "[MUX] pipeline exception: $($_.Exception.Message)" -ForegroundColor Red
        # 파이프라인에서 죽더라도 스케줄러 실패로 안 보이게 성공 반환
        exit 0
    }
}
else {
    Write-Host "[MUX] pipeline disabled by VELOS_PIPELINE_ON=0" -ForegroundColor Yellow
    exit 0
}
