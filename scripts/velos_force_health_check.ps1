# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

# === VELOS: 강제 헬스 체크 실행 ===
# VELOS 환경 준비 및 SystemHealth 태스크 강제 실행

try {
    Write-Host "[VELOS] Starting forced health check..." -ForegroundColor Green

    # 1) VELOS 환경 준비
    Write-Host "1. Preparing VELOS environment..." -ForegroundColor Yellow
    $ROOT = "C:\giwanos"

    # ROOT 디렉토리 확인
    if (-not (Test-Path $ROOT)) {
        Write-Host "[ERROR] VELOS ROOT directory not found: $ROOT" -ForegroundColor Red
        exit 1
    }

    # ROOT 디렉토리로 이동
    cd $ROOT
    Write-Host "   ✅ Changed to VELOS ROOT: $ROOT" -ForegroundColor Green

    # 가상환경 활성화
    $VENV_ACTIVATE = Join-Path $ROOT ".venv_link\Scripts\activate.ps1"
    if (Test-Path $VENV_ACTIVATE) {
        & $VENV_ACTIVATE
        Write-Host "   ✅ Virtual environment activated" -ForegroundColor Green
    }
    else {
        Write-Host "[WARNING] Virtual environment not found: $VENV_ACTIVATE" -ForegroundColor Yellow
    }

    # 2) VELOS-SystemHealth 태스크 강제 실행
    Write-Host "2. Forcing VELOS-SystemHealth task..." -ForegroundColor Yellow

    # 태스크 존재 확인
    $taskExists = schtasks /query /tn "VELOS-SystemHealth" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] VELOS-SystemHealth task not found" -ForegroundColor Red
        Write-Host "   Available tasks:" -ForegroundColor Yellow
        schtasks /query /fo table | Select-String "VELOS"
        exit 1
    }

    # 태스크 강제 실행
    Write-Host "   Executing: schtasks /run /tn 'VELOS-SystemHealth'" -ForegroundColor Cyan
    schtasks /run /tn "VELOS-SystemHealth"
    $taskCode = $LASTEXITCODE

    if ($taskCode -eq 0) {
        Write-Host "   ✅ VELOS-SystemHealth task started successfully" -ForegroundColor Green
    }
    else {
        Write-Host "[ERROR] Failed to start VELOS-SystemHealth task: code=$taskCode" -ForegroundColor Red
        exit $taskCode
    }

    # 3) 실행 상태 확인
    Write-Host "3. Checking task status..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2  # 태스크 시작 대기

    $taskStatus = schtasks /query /tn "VELOS-SystemHealth" /fo csv | ConvertFrom-Csv
    $lastRunTime = $taskStatus."Last Run Time"
    $nextRunTime = $taskStatus."Next Run Time"
    $status = $taskStatus."Status"

    Write-Host "   Last Run Time: $lastRunTime" -ForegroundColor Cyan
    Write-Host "   Next Run Time: $nextRunTime" -ForegroundColor Cyan
    Write-Host "   Status: $status" -ForegroundColor Cyan

    # 4) 헬스 로그 확인
    Write-Host "4. Checking health log..." -ForegroundColor Yellow
    $healthLog = Join-Path $ROOT "data\logs\system_health.json"

    if (Test-Path $healthLog) {
        $healthData = Get-Content $healthLog | ConvertFrom-Json
        $timestamp = $healthData.timestamp
        $overallStatus = $healthData.overall_status

        Write-Host "   Health log timestamp: $timestamp" -ForegroundColor Cyan
        Write-Host "   Overall status: $overallStatus" -ForegroundColor Cyan

        if ($overallStatus -eq "OK") {
            Write-Host "   ✅ Health check completed successfully" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️ Health check completed with issues" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "   ⚠️ Health log not found yet" -ForegroundColor Yellow
    }

    Write-Host "[VELOS] ✅ Forced health check completed" -ForegroundColor Green

}
catch {
    Write-Host "[VELOS] Error during forced health check: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
