# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 워커 알림 실행 스크립트
# Python 경로를 설정하고 VELOS 워커 알림을 실행합니다.

param(
    [switch]$Verbose = $false,

    [switch]$KeepOutput = $false,

    [string]$LogFile = "",

    [string]$Message = ""
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-VelosWorkerNotify {
    param(
        [switch]$Verbose = $false,
        [switch]$KeepOutput = $false,
        [string]$LogFile = "",
        [string]$Message = ""
    )

    $outputFile = if ($LogFile) { $LogFile } else { "$env:TEMP\velos_worker_notify_output.txt" }
    $scriptPath = ".\scripts\worker_notify.py"

    Write-Host "=== VELOS 워커 알림 실행 ==="
    Write-Host "작업 디렉토리: $(Get-Location)"
    Write-Host "스크립트 경로: $scriptPath"
    Write-Host "출력 파일: $outputFile"

    if ($Message) {
        Write-Host "메시지: $Message"
    }

    try {
        # Python 경로 설정
        $env:PYTHONPATH = "C:\giwanos"
        Write-Host "[ENV] PYTHONPATH 설정: $env:PYTHONPATH"

        # 스크립트 경로 확인
        if (-not (Test-Path $scriptPath)) {
            throw "워커 알림 스크립트를 찾을 수 없습니다: $scriptPath"
        }

        Write-Host "[SCRIPT] 스크립트 경로 확인됨: $scriptPath"

        # Python 명령어 구성
        $pythonArgs = @($scriptPath)
        if ($Verbose) {
            $pythonArgs += "--verbose"
        }
        if ($Message) {
            $pythonArgs += "--message", $Message
        }

        $pythonCommand = "python " + ($pythonArgs -join " ")
        Write-Host "[EXECUTE] $pythonCommand"

        # 워커 알림 실행
        $process = Start-Process -FilePath "python" -ArgumentList $pythonArgs -RedirectStandardOutput $outputFile -RedirectStandardError "$outputFile.err" -Wait -PassThru -NoNewWindow

        if ($process.ExitCode -eq 0) {
            Write-Host "[SUCCESS] 워커 알림 실행 완료"

            if (Test-Path $outputFile) {
                $outputContent = Get-Content $outputFile -Raw
                Write-Host "`n=== 워커 알림 출력 ==="
                Write-Host $outputContent
                Write-Host "=== 워커 알림 출력 끝 ==="

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
            Write-Host "[ERROR] 워커 알림 실행 실패 (Exit Code: $($process.ExitCode))"

            # 오류 출력 표시
            if (Test-Path "$outputFile.err") {
                $errorContent = Get-Content "$outputFile.err" -Raw
                Write-Host "`n=== 오류 출력 ==="
                Write-Host $errorContent
                Write-Host "=== 오류 출력 끝 ==="
                Remove-Item "$outputFile.err" -Force
            }
        }

    } catch {
        Write-Host "[ERROR] 워커 알림 실행 실패: $_"
    } finally {
        # 정리
        if (Test-Path $outputFile) {
            if (-not $KeepOutput) { Remove-Item $outputFile -Force -ErrorAction SilentlyContinue }
        }
        if (Test-Path "$outputFile.err") { Remove-Item "$outputFile.err" -Force -ErrorAction SilentlyContinue }
    }
}

# 메인 실행
Invoke-VelosWorkerNotify -Verbose:$Verbose -KeepOutput:$KeepOutput -LogFile $LogFile -Message $Message

Write-Host "`n=== VELOS 워커 알림 실행 완료 ==="
