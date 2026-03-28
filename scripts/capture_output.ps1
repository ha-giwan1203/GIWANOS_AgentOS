# [ACTIVE] VELOS 명령어 출력 캡처 시스템 - 명령어 출력 캡처 유틸리티
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# 명령어 출력 캡처 유틸리티
$ErrorActionPreference = "Stop"

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Capture-CommandOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,

        [string]$Description = "명령어 실행",

        [switch]$ShowOutput = $true,

        [switch]$KeepFile = $false,

        [switch]$DebugOutput = $false,

        [switch]$External = $false
    )

    $tempFile = "$env:TEMP\velos_capture_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

    Write-Host "[CAPTURE] $Description 시작..."
    Write-Host "[COMMAND] $Command"

    try {
        # 명령어 실행 및 출력 캡처
        if ($External) {
            # 외부 PowerShell 7 프로세스에서 실행
            $externalCommand = "pwsh -NoProfile -Command `"$Command 2>&1 | Out-File -Encoding UTF8 '$tempFile'`""
            $process = Start-Process -FilePath "cmd" -ArgumentList "/c", $externalCommand -Wait -PassThru -WindowStyle Hidden

            if ($process.ExitCode -ne 0) {
                throw "외부 프로세스 실행 실패 (Exit Code: $($process.ExitCode))"
            }
        } else {
            # 현재 프로세스에서 실행
            Invoke-Expression "$Command 2>&1" | Out-File -Encoding UTF8 -FilePath $tempFile
        }

        # 캡처된 출력 읽기
        $capturedOutput = Get-Content $tempFile -Raw

        if ($ShowOutput) {
            if ($DebugOutput) {
                Write-Host "`n=== 디버그 출력 (특수 문자 표시) ==="
                $debugContent = $capturedOutput `
                    -replace "`r", "<CR>" `
                    -replace "`n", "<LF>`n" `
                    -replace "`t", "<TAB>" `
                    -replace ([char]27), "<ESC>"
                Write-Host $debugContent
                Write-Host "=== 디버그 출력 끝 ==="
            } else {
                Write-Host "`n=== 캡처된 출력 ==="
                Write-Host $capturedOutput
                Write-Host "=== 출력 끝 ==="
            }
        }

        Write-Host "[SUCCESS] 출력이 캡처되었습니다: $tempFile"

        if (-not $KeepFile) {
            Remove-Item $tempFile -Force
            Write-Host "[CLEANUP] 임시 파일 삭제됨"
        } else {
            Write-Host "[KEEP] 임시 파일 보존됨: $tempFile"
        }

        return $capturedOutput

    } catch {
        Write-Host "[ERROR] 명령어 실행 실패: $_"
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        }
        return $null
    }
}

# 사용 예시
Write-Host "=== VELOS 명령어 출력 캡처 유틸리티 ==="
Write-Host "사용법: Capture-CommandOutput -Command 'your-command' -Description '설명'"
Write-Host ""

# 테스트 실행
$testCommand = "python -c `"import sys, os; print('stdout encoding:', sys.stdout.encoding); print('한글 테스트: 안녕하세요! 🚀✨🎉')`""

Write-Host "테스트 명령어 실행 중..."
$result = Capture-CommandOutput -Command $testCommand -Description "Python UTF-8 테스트"

Write-Host "`n디버그 모드 테스트 실행 중..."
$result = Capture-CommandOutput -Command $testCommand -Description "Python UTF-8 디버그 테스트" -DebugOutput

Write-Host "`n외부 프로세스 테스트 실행 중..."
$result = Capture-CommandOutput -Command $testCommand -Description "Python UTF-8 외부 프로세스 테스트" -External

if ($result) {
    Write-Host "`n[TEST] 캡처 성공!"
} else {
    Write-Host "`n[TEST] 캡처 실패!"
}

Write-Host "`n=== 유틸리티 준비 완료 ==="
