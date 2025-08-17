# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 로그 캡처 스크립트
# 타임스탬프 기반 로그 파일 생성 및 Python 출력을 stdout/stderr로 분리하여 캡처합니다.

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [string]$Command = "print('hello stdout'); import sys; print('hello stderr', file=sys.stderr)",

    [string]$Prefix = "run",

    [switch]$Verbose = $false,

    [switch]$KeepFiles = $false,

    [switch]$ShowContent = $true
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-VelosLogCapture {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [string]$Command = "print('hello stdout'); import sys; print('hello stderr', file=sys.stderr)",
        [string]$Prefix = "run",
        [switch]$Verbose = $false,
        [switch]$KeepFiles = $false,
        [switch]$ShowContent = $true
    )

    Write-Host "=== VELOS 로그 캡처 ==="
    Write-Host "로그 디렉토리: $LogDir"
    Write-Host "명령어: $Command"
    Write-Host "접두사: $Prefix"

    try {
        # 로그 디렉토리 확인 및 생성
        if (!(Test-Path $LogDir)) {
            Write-Host "[CREATE] 로그 디렉토리 생성 중..."
            New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
        }

        # 타임스탬프 생성
        $ts = Get-Date -Format "yyyyMMdd_HHmmss"
        Write-Host "[TIMESTAMP] 생성된 타임스탬프: $ts"

        # 로그 파일 경로 설정
        $stdout = Join-Path $LogDir "$($Prefix)_$ts.out.txt"
        $stderr = Join-Path $LogDir "$($Prefix)_$ts.err.txt"

        Write-Host "[FILES] STDOUT=$stdout"
        Write-Host "[FILES] STDERR=$stderr"

        if ($Verbose) {
            Write-Host "`n=== 실행할 Python 코드 ==="
            Write-Host $Command
            Write-Host "=== Python 코드 끝 ==="
        }

        # Python 명령어 실행 및 출력 캡처
        Write-Host "`n[EXECUTE] Python 명령어 실행 중..."

        $pythonScript = @"
$Command
"@

        # Python 스크립트 실행
        $process = Start-Process -FilePath "python" -ArgumentList "-" -RedirectStandardInput "$env:TEMP\velos_python_input.txt" -RedirectStandardOutput $stdout -RedirectStandardError $stderr -Wait -PassThru -NoNewWindow

        # Python 입력 스크립트 생성
        $pythonScript | Out-File -FilePath "$env:TEMP\velos_python_input.txt" -Encoding UTF8

        if ($process.ExitCode -eq 0) {
            Write-Host "[SUCCESS] Python 명령어 실행 완료 (Exit Code: $($process.ExitCode))"
        } else {
            Write-Host "[WARN] Python 명령어 실행 완료 (Exit Code: $($process.ExitCode))"
        }

        # 파일 크기 확인
        $stdoutSize = if (Test-Path $stdout) { (Get-Item $stdout).Length } else { 0 }
        $stderrSize = if (Test-Path $stderr) { (Get-Item $stderr).Length } else { 0 }

        Write-Host "`n=== 파일 정보 ==="
        Write-Host "STDOUT 크기: $stdoutSize 바이트"
        Write-Host "STDERR 크기: $stderrSize 바이트"

        # 파일 내용 표시
        if ($ShowContent) {
            if (Test-Path $stdout -and $stdoutSize -gt 0) {
                Write-Host "`n=== STDOUT 내용 ==="
                $stdoutContent = Get-Content $stdout -Raw
                Write-Host $stdoutContent
                Write-Host "=== STDOUT 끝 ==="
            } else {
                Write-Host "`n[INFO] STDOUT 파일이 비어있거나 존재하지 않습니다"
            }

            if (Test-Path $stderr -and $stderrSize -gt 0) {
                Write-Host "`n=== STDERR 내용 ==="
                $stderrContent = Get-Content $stderr -Raw
                Write-Host $stderrContent
                Write-Host "=== STDERR 끝 ==="
            } else {
                Write-Host "`n[INFO] STDERR 파일이 비어있거나 존재하지 않습니다"
            }
        }

        # 파일 정리
        if (-not $KeepFiles) {
            Write-Host "`n[CLEANUP] 임시 파일 정리 중..."
            if (Test-Path $stdout) { Remove-Item $stdout -Force }
            if (Test-Path $stderr) { Remove-Item $stderr -Force }
            if (Test-Path "$env:TEMP\velos_python_input.txt") { Remove-Item "$env:TEMP\velos_python_input.txt" -Force }
            Write-Host "[CLEANUP] 임시 파일 삭제 완료"
        } else {
            Write-Host "`n[KEEP] 로그 파일 보존됨:"
            Write-Host "  STDOUT: $stdout"
            Write-Host "  STDERR: $stderr"
        }

        # 결과 반환
        return @{
            "Success" = $true
            "ExitCode" = $process.ExitCode
            "StdoutFile" = $stdout
            "StderrFile" = $stderr
            "StdoutSize" = $stdoutSize
            "StderrSize" = $stderrSize
            "Timestamp" = $ts
        }

    } catch {
        Write-Host "[ERROR] 로그 캡처 실패: $_"
        return @{
            "Success" = $false
            "Error" = $_.Exception.Message
        }
    }
}

function Test-VelosLogCapture {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS 로그 캡처 테스트 ==="

    # 테스트 명령어들
    $testCommands = @(
        @{
            "Name" = "기본 테스트"
            "Command" = "print('hello stdout'); import sys; print('hello stderr', file=sys.stderr)"
        },
        @{
            "Name" = "한글 테스트"
            "Command" = "print('안녕하세요 stdout'); import sys; print('안녕하세요 stderr', file=sys.stderr)"
        },
        @{
            "Name" = "에러 테스트"
            "Command" = "print('정상 출력'); import sys; print('에러 출력', file=sys.stderr); raise Exception('테스트 예외')"
        }
    )

    foreach ($test in $testCommands) {
        Write-Host "`n--- $($test.Name) ---"
        $result = Invoke-VelosLogCapture -LogDir $LogDir -Command $test.Command -Prefix "test" -KeepFiles -ShowContent:$false

        if ($result.Success) {
            Write-Host "✓ $($test.Name) 성공"
            Write-Host "  Exit Code: $($result.ExitCode)"
            Write-Host "  STDOUT 크기: $($result.StdoutSize) 바이트"
            Write-Host "  STDERR 크기: $($result.StderrSize) 바이트"
        } else {
            Write-Host "✗ $($test.Name) 실패: $($result.Error)"
        }
    }
}

# 메인 실행
$result = Invoke-VelosLogCapture -LogDir $LogDir -Command $Command -Prefix $Prefix -Verbose:$Verbose -KeepFiles:$KeepFiles -ShowContent:$ShowContent

if ($result.Success) {
    Write-Host "`n[SUCCESS] VELOS 로그 캡처 완료"
    Write-Host "타임스탬프: $($result.Timestamp)"
    Write-Host "종료 코드: $($result.ExitCode)"
} else {
    Write-Host "`n[FAILED] VELOS 로그 캡처 실패: $($result.Error)"
}

Write-Host "`n=== VELOS 로그 캡처 완료 ==="
