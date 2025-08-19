# [ACTIVE] VELOS 외부 캡처 시스템 - 외부 프로세스 출력 캡처 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# 외부 PowerShell 7 프로세스에서 명령어 실행 및 출력 캡처
# 깨끗한 환경에서 명령어를 실행하여 환경 변수나 프로필의 영향을 제거합니다.

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,

    [string]$OutputFile = "$env:TEMP\raw2.txt",

    [switch]$ShowOutput = $true,

    [switch]$DebugOutput = $false,

    [switch]$HexOutput = $false,

    [switch]$KeepFile = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-ExternalCommand {
    param(
        [string]$Command,
        [string]$OutputFile,
        [switch]$ShowOutput = $true,
        [switch]$DebugOutput = $false,
        [switch]$HexOutput = $false,
        [switch]$KeepFile = $false
    )

    Write-Host "[EXTERNAL] 외부 PowerShell 7에서 명령어 실행"
    Write-Host "[COMMAND] $Command"
    Write-Host "[OUTPUT] $OutputFile"

    try {
        # 외부 PowerShell 7 프로세스에서 명령어 실행
        $externalCommand = "pwsh -NoProfile -Command `"$Command 2>&1 | Out-File -Encoding UTF8 '$OutputFile'`""

        Write-Host "[EXECUTE] $externalCommand"

        # 외부 프로세스 실행
        $process = Start-Process -FilePath "cmd" -ArgumentList "/c", $externalCommand -Wait -PassThru -WindowStyle Hidden

        if ($process.ExitCode -eq 0) {
            Write-Host "[SUCCESS] 외부 명령어 실행 완료"

            if (Test-Path $OutputFile) {
                $fileSize = (Get-Item $OutputFile).Length
                Write-Host "[INFO] 출력 파일 크기: $fileSize 바이트"

                if ($ShowOutput) {
                    try {
                        $capturedOutput = Get-Content $OutputFile -Raw

                        if ($DebugOutput) {
                            Write-Host "`n=== 디버그 출력 (특수 문자 표시) ==="
                            $debugContent = $capturedOutput `
                                -replace "`r", "<CR>" `
                                -replace "`n", "<LF>`n" `
                                -replace "`t", "<TAB>" `
                                -replace ([char]27), "<ESC>"
                            Write-Host $debugContent
                            Write-Host "=== 디버그 출력 끝 ==="
                        } elseif ($HexOutput) {
                            Write-Host "`n=== 16진수 바이트 분석 ==="
                            $bytes = [System.IO.File]::ReadAllBytes($OutputFile)
                            $hexString = ($bytes | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
                            Write-Host $hexString
                            Write-Host "=== 16진수 끝 ==="
                        } else {
                            Write-Host "`n=== 캡처된 출력 ==="
                            Write-Host $capturedOutput
                            Write-Host "=== 출력 끝 ==="
                        }

                    } catch {
                        Write-Host "[ERROR] 출력 파일 읽기 실패: $_"
                    }
                }

                if (-not $KeepFile) {
                    Remove-Item $OutputFile -Force
                    Write-Host "[CLEANUP] 출력 파일 삭제됨"
                } else {
                    Write-Host "[KEEP] 출력 파일 보존됨: $OutputFile"
                }

            } else {
                Write-Host "[WARN] 출력 파일이 생성되지 않았습니다"
            }

        } else {
            Write-Host "[ERROR] 외부 명령어 실행 실패 (Exit Code: $($process.ExitCode))"
        }

    } catch {
        Write-Host "[ERROR] 외부 프로세스 실행 실패: $_"
    }
}

# 메인 실행
Invoke-ExternalCommand -Command $Command -OutputFile $OutputFile -ShowOutput:$ShowOutput -DebugOutput:$DebugOutput -HexOutput:$HexOutput -KeepFile:$KeepFile

Write-Host "`n=== 외부 명령어 실행 완료 ==="



