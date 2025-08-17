# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# Python 표준 입력 덤프 도구 래퍼
# PowerShell에서 Python 덤프 스크립트를 쉽게 사용할 수 있도록 합니다.

param(
    [Parameter(Mandatory=$false)]
    [string]$InputText = "",

    [Parameter(Mandatory=$false)]
    [string]$InputFile = "",

    [switch]$Advanced = $false,

    [switch]$KeepOutput = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-DumpStdout {
    param(
        [string]$InputText = "",
        [string]$InputFile = "",
        [switch]$Advanced = $false,
        [switch]$KeepOutput = $false
    )

    $scriptPath = if ($Advanced) {
        "scripts\dump_stdout_advanced.py"
    } else {
        "scripts\dump_stdout.py"
    }

    $tempFile = "$env:TEMP\velos_dump_input.txt"
    $outputFile = "$env:TEMP\velos_dump_output.txt"

    Write-Host "[DUMP] 표준 입력 덤프 도구 실행"
    Write-Host "[SCRIPT] $scriptPath"

    try {
        # 입력 준비
        if ($InputFile -and (Test-Path $InputFile)) {
            Write-Host "[INPUT] 파일에서 읽기: $InputFile"
            $inputContent = Get-Content $InputFile -Raw
        } elseif ($InputText) {
            Write-Host "[INPUT] 텍스트 입력 사용"
            $inputContent = $InputText
        } else {
            Write-Host "[INPUT] 표준 입력 사용 (대화형 모드)"
            $inputContent = ""
        }

        # 입력을 임시 파일에 저장
        if ($inputContent) {
            $inputContent | Out-File -FilePath $tempFile -Encoding UTF8
            Write-Host "[TEMP] 입력을 임시 파일에 저장: $tempFile"
        }

        # Python 스크립트 실행
        if ($inputContent) {
            # 파일에서 입력 읽기
            $process = Start-Process -FilePath "python" -ArgumentList $scriptPath -RedirectStandardInput $tempFile -RedirectStandardOutput $outputFile -Wait -PassThru -WindowStyle Hidden
        } else {
            # 대화형 모드
            Write-Host "Python 스크립트를 대화형으로 실행합니다. 입력을 입력하세요:"
            $process = Start-Process -FilePath "python" -ArgumentList $scriptPath -RedirectStandardOutput $outputFile -Wait -PassThru -NoNewWindow
        }

        if ($process.ExitCode -eq 0) {
            Write-Host "[SUCCESS] Python 스크립트 실행 완료"

            if (Test-Path $outputFile) {
                $outputContent = Get-Content $outputFile -Raw
                Write-Host "`n=== 덤프 결과 ==="
                Write-Host $outputContent
                Write-Host "=== 덤프 결과 끝 ==="

                if ($KeepOutput) {
                    Write-Host "[KEEP] 출력 파일 보존됨: $outputFile"
                } else {
                    Remove-Item $outputFile -Force
                    Write-Host "[CLEANUP] 출력 파일 삭제됨"
                }
            }
        } else {
            Write-Host "[ERROR] Python 스크립트 실행 실패 (Exit Code: $($process.ExitCode))"
        }

        # 임시 파일 정리
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force
            Write-Host "[CLEANUP] 임시 파일 삭제됨"
        }

    } catch {
        Write-Host "[ERROR] 덤프 실행 실패: $_"

        # 정리
        if (Test-Path $tempFile) { Remove-Item $tempFile -Force -ErrorAction SilentlyContinue }
        if (Test-Path $outputFile) { Remove-Item $outputFile -Force -ErrorAction SilentlyContinue }
    }
}

# 메인 실행
Invoke-DumpStdout -InputText $InputText -InputFile $InputFile -Advanced:$Advanced -KeepOutput:$KeepOutput

Write-Host "`n=== 덤프 도구 실행 완료 ==="
