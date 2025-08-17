# VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# 환경 변수에서 VELOS_ROOT 경로 로드
$velosRoot = $env:VELOS_ROOT
if (-not $velosRoot) {
    # 기본값으로 C:\giwanos 사용
    $velosRoot = "C:\giwanos"
}

# 로그 디렉토리 경로 설정
$logDir = Join-Path $velosRoot "data\logs"

# 로그 디렉토리 존재 확인 및 생성
if (!(Test-Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "로그 디렉토리가 생성되었습니다: $logDir" -ForegroundColor Green
    }
    catch {
        Write-Error "로그 디렉토리 생성 실패: $($_.Exception.Message)"
        exit 1
    }
}

# 타임스탬프 생성
$ts = Get-Date -Format "yyyyMMdd_HHmmss"

# 출력 파일 경로 설정
$stdout = Join-Path $logDir "run_$ts.out.txt"
$stderr = Join-Path $logDir "run_$ts.err.txt"

# Python 스크립트 실행 및 출력 캡처
try {
    @'
print("hello stdout")
import sys; print("hello stderr", file=sys.stderr)
'@ | python - 1> $stdout 2> $stderr

    Write-Host "Python 스크립트 실행 완료" -ForegroundColor Green
    Write-Host "STDOUT=$stdout" -ForegroundColor Cyan
    Write-Host "STDERR=$stderr" -ForegroundColor Cyan

    # 자가 검증: 출력 파일 존재 확인
    if (Test-Path $stdout) {
        Write-Host "=== STDOUT 내용 ===" -ForegroundColor Yellow
        Get-Content $stdout -Raw
    } else {
        Write-Warning "STDOUT 파일이 생성되지 않았습니다: $stdout"
    }

    if (Test-Path $stderr) {
        Write-Host "=== STDERR 내용 ===" -ForegroundColor Red
        Get-Content $stderr -Raw
    } else {
        Write-Warning "STDERR 파일이 생성되지 않았습니다: $stderr"
    }

    # 실행 결과 요약
    $stdoutSize = if (Test-Path $stdout) { (Get-Item $stdout).Length } else { 0 }
    $stderrSize = if (Test-Path $stderr) { (Get-Item $stderr).Length } else { 0 }

    Write-Host "실행 완료 - STDOUT: ${stdoutSize}바이트, STDERR: ${stderrSize}바이트" -ForegroundColor Green

} catch {
    Write-Error "Python 스크립트 실행 실패: $($_.Exception.Message)"
    exit 1
}
