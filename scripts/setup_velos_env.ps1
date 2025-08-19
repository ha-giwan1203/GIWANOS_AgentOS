# [ACTIVE] VELOS 환경 설정 시스템 - 통합 환경변수 설정 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

Write-Host "=== VELOS 통합 환경변수 설정 ===" -ForegroundColor Yellow

# VELOS 시스템 환경변수 설정
$envVars = @{
    "VELOS_ROOT" = "C:\giwanos"
    "VELOS_VENV" = "C:\Users\User\venvs\velos"
    "VELOS_PYTHON" = "C:\Users\User\venvs\velos\Scripts\python.exe"
    "VELOS_DB" = "C:\giwanos\data\velos.db"
    "VELOS_LOG_PATH" = "C:\giwanos\data\logs"
    "VELOS_BACKUP" = "C:\giwanos\data\backups"
    "VELOS_LOG_LEVEL" = "INFO"
    "VELOS_API_TIMEOUT" = "30"
    "VELOS_API_RETRIES" = "3"
    "VELOS_MAX_WORKERS" = "4"
    "VELOS_DEBUG" = "false"
    # 디스패치 채널 설정
    "DISPATCH_EMAIL" = "1"
    "DISPATCH_SLACK" = "1"
    "DISPATCH_NOTION" = "1"
    "DISPATCH_PUSH" = "1"
}

Write-Host "`n[1] 현재 세션 환경변수 설정..." -ForegroundColor Cyan
foreach ($key in $envVars.Keys) {
    Set-Item -Path "env:$key" -Value $envVars[$key]
    Write-Host "  $key = $($envVars[$key])" -ForegroundColor Green
}

Write-Host "`n[2] 시스템 환경변수 영구 설정..." -ForegroundColor Cyan
foreach ($key in $envVars.Keys) {
    try {
        [Environment]::SetEnvironmentVariable($key, $envVars[$key], "User")
        Write-Host "  $key 영구 설정 완료" -ForegroundColor Green
    }
    catch {
        Write-Host "  $key 설정 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[3] 로그 디렉토리 설정..." -ForegroundColor Cyan
$logDir = Join-Path $envVars["VELOS_ROOT"] "data\logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "  ✅ 로그 디렉토리 생성: $logDir" -ForegroundColor Green
} else {
    Write-Host "  ✅ 로그 디렉토리 존재: $logDir" -ForegroundColor Green
}

Write-Host "`n[4] 환경변수 설정 검증..." -ForegroundColor Cyan
python -c "import sys; sys.path.append('.'); from configs import get_setting; print('VELOS_ROOT:', get_setting('root')); print('VELOS_DB:', get_setting('database.path')); print('VELOS_LOG:', get_setting('logging.path'))"

Write-Host "`n[5] 채널 설정 상태 확인..." -ForegroundColor Cyan
$channels = @("DISPATCH_EMAIL", "DISPATCH_SLACK", "DISPATCH_NOTION", "DISPATCH_PUSH")
foreach ($channel in $channels) {
    $value = [Environment]::GetEnvironmentVariable($channel, "User")
    $status = if ($value -eq "1") { "✅ 활성화" } else { "❌ 비활성화" }
    Write-Host "  $channel : $status" -ForegroundColor $(if ($value -eq "1") { "Green" } else { "Red" })
}

Write-Host "`n=== VELOS 통합 환경변수 설정 완료 ===" -ForegroundColor Green
Write-Host "새 터미널 세션에서 환경변수가 적용됩니다." -ForegroundColor Yellow


