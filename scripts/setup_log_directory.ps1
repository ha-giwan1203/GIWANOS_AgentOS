# VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# 환경 변수에서 VELOS_ROOT 경로 로드
$velosRoot = $env:VELOS_ROOT
if (-not $velosRoot) {
    # 기본값으로 C:\giwanos 사용
    $velosRoot = "C:\giwanos"
}

# 로그 디렉토리 경로 설정
$logDir = Join-Path $velosRoot "data\logs"

# 디렉토리 존재 확인 및 생성
if (!(Test-Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "로그 디렉토리가 생성되었습니다: $logDir" -ForegroundColor Green
    }
    catch {
        Write-Error "로그 디렉토리 생성 실패: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "로그 디렉토리가 이미 존재합니다: $logDir" -ForegroundColor Yellow
}

# 자가 검증: 디렉토리 접근 가능 여부 확인
try {
    $testFile = Join-Path $logDir "test_access.tmp"
    New-Item -ItemType File -Path $testFile -Force | Out-Null
    Remove-Item $testFile -Force
    Write-Host "로그 디렉토리 접근 검증 완료" -ForegroundColor Green
}
catch {
    Write-Error "로그 디렉토리 접근 검증 실패: $($_.Exception.Message)"
    exit 1
}

Write-Host "VELOS 로그 디렉토리 설정이 완료되었습니다." -ForegroundColor Green
