# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 워커 메모리 실행 스크립트
# Python 경로를 설정하고 VELOS 워커 메모리를 실행합니다.

param(
    [switch]$Verbose = $false,

    [switch]$KeepOutput = $false,

    [string]$LogFile = "",

    [switch]$Background = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Start-VelosWorkerMemory {
    param(
        [switch]$Verbose = $false,
        [switch]$KeepOutput = $false,
        [string]$LogFile = "",
        [switch]$Background = $false
    )

    $outputFile = if ($LogFile) { $LogFile } else { "$env:TEMP\velos_worker_memory_output.txt" }
    $scriptPath = ".\scripts\worker_memory.py"

    Write-Host "=== VELOS 워커 메모리 실행 ==="
    Write-Host "작업 디렉토리: $(Get-Location)"
    Write-Host "스크립트 경로: $scriptPath"
    Write-Host "출력 파일: $outputFile"

    try {
        # Python 경로 설정
        $env:PYTHONPATH = "C:\giwanos"
        Write-Host "[ENV] PYTHONPATH 설정: $env:PYTHONPATH"

        # 스크립트 경로 확인
        if (-not (Test-Path $scriptPath)) {
            throw "워커 메모리 스크립트를 찾을 수 없습니다: $scriptPath"
        }

        Write-Host "[SCRIPT] 스크립트 경로 확인됨: $scriptPath"

        # Python 명령어 구성
        $pythonArgs = @($scriptPath)
        if ($Verbose) {
            $pythonArgs += "--verbose"
        }

        $pythonCommand = "python " + ($pythonArgs -join " ")
        Write-Host "[EXECUTE] $pythonCommand"

        if ($Background) {
            # 백그라운드 실행
            Write-Host "[BACKGROUND] 백그라운드에서 워커 메모리 실행"
            $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -RedirectStandardOutput $outputFile -RedirectStandardError "$outputFile.err" -WindowStyle Hidden -PassThru

            Write-Host "[INFO] 백그라운드 프로세스 시작됨 (PID: $($process.Id))"
            Write-Host "[INFO] 출력이 다음 파일에 기록됩니다: $outputFile"

            if ($KeepOutput) {
                Write-Host "[KEEP] 출력 파일이 보존됩니다: $outputFile"
            }

        } else {
            # 포그라운드 실행
            Write-Host "[FOREGROUND] 포그라운드에서 워커 메모리 실행"
            $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -RedirectStandardOutput $outputFile -RedirectStandardError "$outputFile.err" -Wait -PassThru -NoNewWindow

            if ($process.ExitCode -eq 0) {
                Write-Host "[SUCCESS] 워커 메모리 실행 완료"

                if (Test-Path $outputFile) {
                    $outputContent = Get-Content $outputFile -Raw
                    Write-Host "`n=== 워커 메모리 출력 ==="
                    Write-Host $outputContent
                    Write-Host "=== 워커 메모리 출력 끝 ==="

                    if (-not $KeepOutput) {
                        Remove-Item $outputFile -Force
                        Write-Host "[CLEANUP] 출력 파일 삭제됨"
                    } else {
                        Write-Host "[KEEP] 출력 파일 보존됨: $outputFile"
                    }
                }

                # 오류 출력 확인
                if (Test-Path "$outputFile.err") {
                    $errorContent = Get-Content "$outputFile.err" -Raw
                    if ($errorContent) {
                        Write-Host "`n=== 오류 출력 ==="
                        Write-Host $errorContent
                        Write-Host "=== 오류 출력 끝 ==="
                    }
                    Remove-Item "$outputFile.err" -Force
                }

            } else {
                Write-Host "[ERROR] 워커 메모리 실행 실패 (Exit Code: $($process.ExitCode))"

                # 오류 출력 표시
                if (Test-Path "$outputFile.err") {
                    $errorContent = Get-Content "$outputFile.err" -Raw
                    Write-Host "`n=== 오류 출력 ==="
                    Write-Host $errorContent
                    Write-Host "=== 오류 출력 끝 ==="
                    Remove-Item "$outputFile.err" -Force
                }
            }
        }

    } catch {
        Write-Host "[ERROR] 워커 메모리 실행 실패: $_"
    } finally {
        # 정리 (포그라운드 실행 시에만)
        if (-not $Background) {
            if (Test-Path $outputFile) {
                if (-not $KeepOutput) { Remove-Item $outputFile -Force -ErrorAction SilentlyContinue }
            }
            if (Test-Path "$outputFile.err") { Remove-Item "$outputFile.err" -Force -ErrorAction SilentlyContinue }
        }
    }
}

# 메인 실행
Start-VelosWorkerMemory -Verbose:$Verbose -KeepOutput:$KeepOutput -LogFile $LogFile -Background:$Background

Write-Host "`n=== VELOS 워커 메모리 실행 완료 ==="
