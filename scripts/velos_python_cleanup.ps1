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
$logFile = Join-Path $logDir "python_cleanup_$ts.log"

Write-Host "VELOS Python 프로세스 정리 시작..." -ForegroundColor Cyan

try {
    # 현재 실행 중인 Python 프로세스 확인
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

    if ($pythonProcesses) {
        Write-Host "발견된 Python 프로세스 수: $($pythonProcesses.Count)개" -ForegroundColor Yellow

        # 프로세스 정보 로깅
        $processInfo = @()
        foreach ($proc in $pythonProcesses) {
            $processInfo += [PSCustomObject]@{
                PID = $proc.Id
                ProcessName = $proc.ProcessName
                StartTime = $proc.StartTime
                CPU = $proc.CPU
                WorkingSet = [math]::Round($proc.WorkingSet / 1MB, 2)
            }
        }

        # 프로세스 정보를 로그 파일에 저장
        $processInfo | Format-Table -AutoSize | Out-File -FilePath $logFile -Encoding UTF8
        Write-Host "프로세스 정보가 로그에 저장되었습니다: $logFile" -ForegroundColor Green

        # 프로세스 목록 표시
        Write-Host "=== 종료 대상 프로세스 ===" -ForegroundColor Red
        $processInfo | Format-Table -AutoSize

        # 사용자 확인 (선택사항)
        $confirm = Read-Host "위의 Python 프로세스들을 종료하시겠습니까? (Y/N)"
        if ($confirm -eq 'Y' -or $confirm -eq 'y') {
            # 프로세스 강제 종료
            $stoppedProcesses = $pythonProcesses | Stop-Process -Force -PassThru

            Write-Host "Python 프로세스 종료 완료" -ForegroundColor Green
            Write-Host "종료된 프로세스 수: $($stoppedProcesses.Count)개" -ForegroundColor Green

            # 종료 결과를 로그에 추가
            "=== 종료 완료 ===" | Out-File -FilePath $logFile -Encoding UTF8 -Append
            "종료 시간: $(Get-Date)" | Out-File -FilePath $logFile -Encoding UTF8 -Append
            "종료된 프로세스 수: $($stoppedProcesses.Count)개" | Out-File -FilePath $logFile -Encoding UTF8 -Append

            # 자가 검증: 프로세스가 실제로 종료되었는지 확인
            Start-Sleep -Seconds 2
            $remainingProcesses = Get-Process python -ErrorAction SilentlyContinue

            if ($remainingProcesses) {
                Write-Warning "일부 Python 프로세스가 여전히 실행 중입니다: $($remainingProcesses.Count)개"
                "경고: 일부 프로세스가 여전히 실행 중" | Out-File -FilePath $logFile -Encoding UTF8 -Append
            } else {
                Write-Host "모든 Python 프로세스가 성공적으로 종료되었습니다." -ForegroundColor Green
                "모든 프로세스 종료 확인됨" | Out-File -FilePath $logFile -Encoding UTF8 -Append
            }

        } else {
            Write-Host "프로세스 종료가 취소되었습니다." -ForegroundColor Yellow
            "사용자에 의해 취소됨" | Out-File -FilePath $logFile -Encoding UTF8 -Append
        }

    } else {
        Write-Host "실행 중인 Python 프로세스가 없습니다." -ForegroundColor Green
        "실행 중인 Python 프로세스 없음" | Out-File -FilePath $logFile -Encoding UTF8
    }

    # 정리 작업 완료 로그
    "=== 정리 작업 완료 ===" | Out-File -FilePath $logFile -Encoding UTF8 -Append
    "완료 시간: $(Get-Date)" | Out-File -FilePath $logFile -Encoding UTF8 -Append

    Write-Host "Python 프로세스 정리 작업이 완료되었습니다." -ForegroundColor Green
    Write-Host "로그 파일: $logFile" -ForegroundColor Cyan

} catch {
    Write-Error "Python 프로세스 정리 중 오류 발생: $($_.Exception.Message)"
    "오류 발생: $($_.Exception.Message)" | Out-File -FilePath $logFile -Encoding UTF8 -Append
    exit 1
}
