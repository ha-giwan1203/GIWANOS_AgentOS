# [ACTIVE] VELOS Python 프로세스 종료 시스템 - Python 프로세스 종료 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Python 프로세스 종료 스크립트
# 실행 중인 모든 Python 프로세스를 안전하게 종료합니다.

param(
    [string]$ProcessName = "python",

    [switch]$Force = $true,

    [switch]$Verbose = $false,

    [switch]$DryRun = $false,

    [switch]$ShowProcesses = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Stop-VelosPythonProcesses {
    param(
        [string]$ProcessName = "python",
        [switch]$Force = $true,
        [switch]$Verbose = $false,
        [switch]$DryRun = $false,
        [switch]$ShowProcesses = $false
    )

    Write-Host "=== VELOS Python 프로세스 종료 ==="
    Write-Host "프로세스 이름: $ProcessName"
    Write-Host "강제 종료: $Force"
    Write-Host "드라이 런: $DryRun"

    try {
        # 실행 중인 Python 프로세스 확인
        Write-Host "`n[SCAN] 실행 중인 $ProcessName 프로세스 검색 중..."
        $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue

        if ($processes) {
            $processCount = $processes.Count
            Write-Host "[FOUND] $processCount 개의 $ProcessName 프로세스 발견"

            if ($ShowProcesses) {
                Write-Host "`n=== 프로세스 목록 ==="
                $processes | ForEach-Object {
                    $cpu = if ($_.CPU) { "$([math]::Round($_.CPU, 2))" } else { "N/A" }
                    $memory = [math]::Round($_.WorkingSet64 / 1MB, 2)
                    Write-Host "PID: $($_.Id), CPU: $cpu, Memory: ${memory}MB, StartTime: $($_.StartTime)"
                }
                Write-Host "=== 프로세스 목록 끝 ==="
            }

            if ($DryRun) {
                Write-Host "`n[DRY-RUN] 종료할 프로세스 목록:"
                $processes | ForEach-Object {
                    Write-Host "  - PID: $($_.Id), CPU: $([math]::Round($_.CPU, 2)), Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2))MB"
                }
                Write-Host "[DRY-RUN] 실제로는 프로세스를 종료하지 않습니다."
            } else {
                Write-Host "`n[KILL] $ProcessName 프로세스 종료 시작..."

                # 프로세스 종료
                $killedProcesses = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Stop-Process -Force -PassThru

                if ($killedProcesses) {
                    $killedCount = $killedProcesses.Count
                    Write-Host "[SUCCESS] $killedCount 개의 $ProcessName 프로세스 종료 완료"

                    if ($Verbose) {
                        Write-Host "`n=== 종료된 프로세스 목록 ==="
                        $killedProcesses | ForEach-Object {
                            Write-Host "  - PID: $($_.Id) (종료됨)"
                        }
                        Write-Host "=== 종료된 프로세스 목록 끝 ==="
                    }

                    # 종료 확인
                    Start-Sleep -Seconds 1
                    $remainingProcesses = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue

                    if ($remainingProcesses) {
                        $remainingCount = $remainingProcesses.Count
                        Write-Host "[WARN] $remainingCount 개의 $ProcessName 프로세스가 여전히 실행 중입니다"

                        if ($Verbose) {
                            Write-Host "`n=== 남은 프로세스 목록 ==="
                            $remainingProcesses | ForEach-Object {
                                Write-Host "  - PID: $($_.Id), CPU: $([math]::Round($_.CPU, 2)), Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2))MB"
                            }
                            Write-Host "=== 남은 프로세스 목록 끝 ==="
                        }
                    } else {
                        Write-Host "[SUCCESS] 모든 $ProcessName 프로세스가 성공적으로 종료되었습니다"
                    }

                    return @{
                        "Success" = $true
                        "KilledCount" = $killedCount
                        "RemainingCount" = if ($remainingProcesses) { $remainingProcesses.Count } else { 0 }
                        "Processes" = $killedProcesses
                    }

                } else {
                    Write-Host "[WARN] 종료할 $ProcessName 프로세스가 없습니다"
                    return @{
                        "Success" = $true
                        "KilledCount" = 0
                        "RemainingCount" = 0
                        "Processes" = @()
                    }
                }
            }

        } else {
            Write-Host "[INFO] 실행 중인 $ProcessName 프로세스가 없습니다"
            return @{
                "Success" = $true
                "KilledCount" = 0
                "RemainingCount" = 0
                "Processes" = @()
            }
        }

    } catch {
        Write-Host "[ERROR] Python 프로세스 종료 실패: $_"
        return @{
            "Success" = $false
            "Error" = $_.Exception.Message
            "KilledCount" = 0
            "RemainingCount" = 0
            "Processes" = @()
        }
    }
}

function Test-VelosPythonProcesses {
    param(
        [string]$ProcessName = "python"
    )

    Write-Host "=== VELOS Python 프로세스 상태 확인 ==="

    try {
        $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue

        if ($processes) {
            $processCount = $processes.Count
            Write-Host "✓ $processCount 개의 $ProcessName 프로세스가 실행 중입니다"

            Write-Host "`n=== 프로세스 상세 정보 ==="
            $totalMemory = 0
            $totalCpu = 0

            $processes | ForEach-Object {
                $memory = $_.WorkingSet64 / 1MB
                $cpu = if ($_.CPU) { $_.CPU } else { 0 }
                $totalMemory += $memory
                $totalCpu += $cpu

                Write-Host "PID: $($_.Id)"
                Write-Host "  CPU: $([math]::Round($cpu, 2))"
                Write-Host "  Memory: $([math]::Round($memory, 2))MB"
                Write-Host "  StartTime: $($_.StartTime)"
                Write-Host "  ProcessName: $($_.ProcessName)"
                Write-Host ""
            }

            Write-Host "=== 요약 ==="
            Write-Host "총 프로세스 수: $processCount"
            Write-Host "총 메모리 사용량: $([math]::Round($totalMemory, 2))MB"
            Write-Host "총 CPU 사용량: $([math]::Round($totalCpu, 2))"

        } else {
            Write-Host "✓ 실행 중인 $ProcessName 프로세스가 없습니다"
        }

    } catch {
        Write-Host "[ERROR] 프로세스 상태 확인 실패: $_"
    }
}

function Start-VelosPythonProcesses {
    param(
        [string]$Command = "python -c 'print(\"Hello, VELOS!\")'",
        [int]$Count = 1,
        [switch]$Verbose = $false
    )

    Write-Host "=== VELOS Python 프로세스 시작 ==="
    Write-Host "명령어: $Command"
    Write-Host "개수: $Count"

    $startedProcesses = @()

    for ($i = 1; $i -le $Count; $i++) {
        try {
            Write-Host "`n[START] Python 프로세스 $i 시작 중..."
            $process = Start-Process -FilePath "python" -ArgumentList "-c", "print('Hello, VELOS! Process $i')" -PassThru -WindowStyle Hidden

            if ($process) {
                $startedProcesses += $process
                Write-Host "[SUCCESS] 프로세스 $i 시작됨 (PID: $($process.Id))"
            } else {
                Write-Host "[ERROR] 프로세스 $i 시작 실패"
            }

        } catch {
            Write-Host "[ERROR] 프로세스 $i 시작 실패: $_"
        }
    }

    Write-Host "`n[SUMMARY] $($startedProcesses.Count) 개의 Python 프로세스 시작 완료"

    return $startedProcesses
}

# 메인 실행
$result = Stop-VelosPythonProcesses -ProcessName $ProcessName -Force:$Force -Verbose:$Verbose -DryRun:$DryRun -ShowProcesses:$ShowProcesses

if ($result.Success) {
    Write-Host "`n[SUCCESS] VELOS Python 프로세스 종료 완료"
    Write-Host "종료된 프로세스 수: $($result.KilledCount)"
    Write-Host "남은 프로세스 수: $($result.RemainingCount)"
} else {
    Write-Host "`n[FAILED] VELOS Python 프로세스 종료 실패: $($result.Error)"
}

Write-Host "`n=== VELOS Python 프로세스 종료 완료 ==="



