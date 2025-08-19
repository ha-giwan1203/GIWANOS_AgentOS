# [ACTIVE] VELOS Tee 로그 시스템 - 로그 파일 및 콘솔 동시 출력 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Tee 로그 스크립트
# 명령어 실행 결과를 로그 파일에 저장하면서 동시에 콘솔에 출력합니다.

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [string]$Command = "python -c 'print(\"Hello, VELOS!\")'",

    [string]$Prefix = "tee",

    [switch]$Verbose = $false,

    [switch]$KeepLog = $false,

    [switch]$ShowLogPath = $true,

    [switch]$AppendTimestamp = $true
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-VelosTeeLog {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [string]$Command = "python -c 'print(\"Hello, VELOS!\")'",
        [string]$Prefix = "tee",
        [switch]$Verbose = $false,
        [switch]$KeepLog = $false,
        [switch]$ShowLogPath = $true,
        [switch]$AppendTimestamp = $true
    )

    Write-Host "=== VELOS Tee 로그 실행 ==="
    Write-Host "명령어: $Command"
    Write-Host "로그 디렉토리: $LogDir"
    Write-Host "접두사: $Prefix"

    try {
        # 로그 디렉토리 확인 및 생성
        if (!(Test-Path $LogDir)) {
            Write-Host "[CREATE] 로그 디렉토리 생성 중..."
            New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        }

        # 로그 파일 경로 생성
        $timestamp = if ($AppendTimestamp) { Get-Date -Format "yyyyMMdd_HHmmss" } else { "" }
        $logFileName = if ($timestamp) { "${Prefix}_${timestamp}.log" } else { "${Prefix}.log" }
        $logFilePath = Join-Path $LogDir $logFileName

        Write-Host "[LOG] 로그 파일: $logFilePath"

        if ($Verbose) {
            Write-Host "`n=== 실행할 명령어 ==="
            Write-Host $Command
            Write-Host "=== 명령어 끝 ==="
        }

        # 명령어 실행 및 Tee 로그
        Write-Host "`n[EXECUTE] 명령어 실행 중..."
        $startTime = Get-Date

        # Tee-Object를 사용하여 로그 파일과 콘솔에 동시 출력
        $result = Invoke-Expression "$Command 2>&1" | Tee-Object -FilePath $logFilePath | Out-Host

        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds

        Write-Host "`n[SUCCESS] 명령어 실행 완료 (소요시간: $([math]::Round($duration, 2)) 초)"

        # 로그 파일 정보 확인
        if (Test-Path $logFilePath) {
            $logFileSize = (Get-Item $logFilePath).Length
            $logFileLines = (Get-Content $logFilePath | Measure-Object -Line).Lines

            Write-Host "`n=== 로그 파일 정보 ==="
            Write-Host "파일 경로: $logFilePath"
            Write-Host "파일 크기: $logFileSize 바이트"
            Write-Host "라인 수: $logFileLines"

            if ($ShowLogPath) {
                Write-Host "로그 파일 경로: $logFilePath"
            }

            # 로그 파일 내용 미리보기 (요청 시)
            if ($Verbose) {
                Write-Host "`n=== 로그 파일 내용 미리보기 ==="
                $logContent = Get-Content $logFilePath -Head 10
                $logContent | ForEach-Object { Write-Host $_ }
                if ($logFileLines -gt 10) {
                    Write-Host "... (총 $logFileLines 라인 중 처음 10라인만 표시)"
                }
                Write-Host "=== 로그 파일 내용 끝 ==="
            }

            # 로그 파일 정리
            if (-not $KeepLog) {
                Write-Host "`n[CLEANUP] 로그 파일 삭제 중..."
                Remove-Item $logFilePath -Force
                Write-Host "[CLEANUP] 로그 파일 삭제 완료"
            } else {
                Write-Host "`n[KEEP] 로그 파일 보존됨: $logFilePath"
            }

            return @{
                "Success" = $true
                "LogFilePath" = $logFilePath
                "LogFileSize" = $logFileSize
                "LogFileLines" = $logFileLines
                "Duration" = $duration
                "StartTime" = $startTime
                "EndTime" = $endTime
            }

        } else {
            Write-Host "[WARN] 로그 파일이 생성되지 않았습니다"
            return @{
                "Success" = $false
                "Error" = "로그 파일이 생성되지 않음"
                "Duration" = $duration
            }
        }

    } catch {
        Write-Host "[ERROR] Tee 로그 실행 실패: $_"
        return @{
            "Success" = $false
            "Error" = $_.Exception.Message
        }
    }
}

function Test-VelosTeeLog {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS Tee 로그 테스트 ==="

    # 테스트 시나리오들
    $testScenarios = @(
        @{
            "Name" = "기본 출력 테스트"
            "Command" = "python -c 'print(\"Hello, VELOS!\")'"
            "Prefix" = "test_basic"
        },
        @{
            "Name" = "한글 출력 테스트"
            "Command" = "python -c 'print(\"안녕하세요, VELOS!\")'"
            "Prefix" = "test_korean"
        },
        @{
            "Name" = "에러 출력 테스트"
            "Command" = "python -c 'import sys; print(\"정상 출력\"); print(\"에러 출력\", file=sys.stderr)'"
            "Prefix" = "test_error"
        },
        @{
            "Name" = "복잡한 명령어 테스트"
            "Command" = "python -c 'import os; print(\"현재 디렉토리:\", os.getcwd()); print(\"환경 변수 PYTHONPATH:\", os.getenv(\"PYTHONPATH\", \"설정되지 않음\"))'"
            "Prefix" = "test_complex"
        }
    )

    foreach ($test in $testScenarios) {
        Write-Host "`n--- $($test.Name) ---"
        $result = Invoke-VelosTeeLog -LogDir $LogDir -Command $test.Command -Prefix $test.Prefix -KeepLog -ShowLogPath:$false

        if ($result.Success) {
            Write-Host "✓ $($test.Name) 성공"
            Write-Host "  로그 파일 크기: $($result.LogFileSize) 바이트"
            Write-Host "  로그 라인 수: $($result.LogFileLines)"
            Write-Host "  소요시간: $([math]::Round($result.Duration, 2)) 초"
        } else {
            Write-Host "✗ $($test.Name) 실패: $($result.Error)"
        }
    }
}

function Get-VelosTeeLogHistory {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [string]$Prefix = "tee",
        [int]$MaxFiles = 10
    )

    Write-Host "=== VELOS Tee 로그 히스토리 ==="
    Write-Host "로그 디렉토리: $LogDir"
    Write-Host "접두사: $Prefix"

    try {
        $pattern = "$Prefix*.log"
        $logFiles = Get-ChildItem -Path $LogDir -Filter $pattern | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxFiles

        if ($logFiles) {
            Write-Host "`n=== 최근 로그 파일 목록 ==="
            $logFiles | ForEach-Object {
                $size = [math]::Round($_.Length / 1KB, 2)
                $lines = (Get-Content $_.FullName | Measure-Object -Line).Lines
                Write-Host "$($_.Name)"
                Write-Host "  크기: ${size}KB, 라인: $lines, 수정일: $($_.LastWriteTime)"
            }
            Write-Host "=== 로그 파일 목록 끝 ==="
        } else {
            Write-Host "[INFO] $pattern 패턴의 로그 파일이 없습니다"
        }

    } catch {
        Write-Host "[ERROR] 로그 히스토리 조회 실패: $_"
    }
}

# 메인 실행
$result = Invoke-VelosTeeLog -LogDir $LogDir -Command $Command -Prefix $Prefix -Verbose:$Verbose -KeepLog:$KeepLog -ShowLogPath:$ShowLogPath -AppendTimestamp:$AppendTimestamp

if ($result.Success) {
    Write-Host "`n[SUCCESS] VELOS Tee 로그 완료"
    Write-Host "로그 파일: $($result.LogFilePath)"
    Write-Host "파일 크기: $($result.LogFileSize) 바이트"
    Write-Host "라인 수: $($result.LogFileLines)"
    Write-Host "소요시간: $([math]::Round($result.Duration, 2)) 초"
} else {
    Write-Host "`n[FAILED] VELOS Tee 로그 실패: $($result.Error)"
}

Write-Host "`n=== VELOS Tee 로그 완료 ==="



