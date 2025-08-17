# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 타임아웃 캡처 스크립트
# 타임아웃 기능이 있는 고급 프로세스 실행 및 비동기 출력 캡처

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [string]$Command = "import time; print('start'); time.sleep(999); print('end')",

    [int]$TimeoutSec = 30,

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

function Invoke-VelosTimeoutCapture {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [string]$Command = "import time; print('start'); time.sleep(999); print('end')",
        [int]$TimeoutSec = 30,
        [string]$Prefix = "run",
        [switch]$Verbose = $false,
        [switch]$KeepFiles = $false,
        [switch]$ShowContent = $true
    )

    Write-Host "=== VELOS 타임아웃 캡처 ==="
    Write-Host "로그 디렉토리: $LogDir"
    Write-Host "명령어: $Command"
    Write-Host "타임아웃: $TimeoutSec 초"
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

        # ProcessStartInfo 설정
        Write-Host "`n[PROCESS] 프로세스 설정 중..."
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "-"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardInput = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
        $psi.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)

        # 프로세스 생성 및 시작
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $psi
        $null = $proc.Start()

        Write-Host "[PROCESS] 프로세스 시작됨 (PID: $($proc.Id))"

        # 코드 주입
        Write-Host "[INPUT] Python 코드 주입 중..."
        $code = @"
$Command
"@
        $proc.StandardInput.Write($code)
        $proc.StandardInput.Close()
        Write-Host "[INPUT] 코드 주입 완료"

        # 비동기 출력 캡처
        Write-Host "[CAPTURE] 비동기 출력 캡처 시작..."
        $so = New-Object System.IO.StreamWriter($stdout, $false, [Text.UTF8Encoding]::new($false))
        $se = New-Object System.IO.StreamWriter($stderr, $false, [Text.UTF8Encoding]::new($false))

        # 출력 이벤트 핸들러 설정
        $proc.OutputDataReceived += {
            param($sender, $e)
            if ($e.Data) {
                $so.WriteLine($e.Data)
                $so.Flush()
                if ($Verbose) { Write-Host "[STDOUT] $($e.Data)" }
            }
        }

        $proc.ErrorDataReceived += {
            param($sender, $e)
            if ($e.Data) {
                $se.WriteLine($e.Data)
                $se.Flush()
                if ($Verbose) { Write-Host "[STDERR] $($e.Data)" }
            }
        }

        # 비동기 읽기 시작
        $proc.BeginOutputReadLine()
        $proc.BeginErrorReadLine()

        # 타임아웃 감시
        Write-Host "[TIMEOUT] 타임아웃 감시 시작 ($TimeoutSec 초)..."
        $startTime = Get-Date
        $timedOut = $false

        if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
            $timedOut = $true
            Write-Host "[TIMEOUT] 타임아웃 발생! 프로세스 종료 중..."
            try {
                $proc.Kill($true)
                Write-Host "[TIMEOUT] 프로세스 강제 종료됨 (PID: $($proc.Id))"
            } catch {
                Write-Host "[ERROR] 프로세스 종료 실패: $_"
            }

            # 타임아웃 메시지를 stderr에 기록
            $timeoutMsg = "TIMEOUT $TimeoutSec sec. Killed PID=$($proc.Id)"
            $se.WriteLine($timeoutMsg)
            $se.Flush()
            Write-Host "[TIMEOUT] $timeoutMsg"
        } else {
            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds
            Write-Host "[SUCCESS] 프로세스 정상 종료 (소요시간: $([math]::Round($duration, 2)) 초)"
        }

        # 스트림 정리
        $so.Close()
        $se.Close()

        # 파일 크기 확인
        $stdoutSize = if (Test-Path $stdout) { (Get-Item $stdout).Length } else { 0 }
        $stderrSize = if (Test-Path $stderr) { (Get-Item $stderr).Length } else { 0 }

        Write-Host "`n=== 파일 정보 ==="
        Write-Host "STDOUT 크기: $stdoutSize 바이트"
        Write-Host "STDERR 크기: $stderrSize 바이트"
        Write-Host "타임아웃 발생: $timedOut"

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
            Write-Host "[CLEANUP] 임시 파일 삭제 완료"
        } else {
            Write-Host "`n[KEEP] 로그 파일 보존됨:"
            Write-Host "  STDOUT: $stdout"
            Write-Host "  STDERR: $stderr"
        }

        # 결과 반환
        return @{
            "Success" = $true
            "ExitCode" = $proc.ExitCode
            "StdoutFile" = $stdout
            "StderrFile" = $stderr
            "StdoutSize" = $stdoutSize
            "StderrSize" = $stderrSize
            "Timestamp" = $ts
            "TimedOut" = $timedOut
            "ProcessId" = $proc.Id
            "Duration" = if ($timedOut) { $TimeoutSec } else { ($endTime - $startTime).TotalSeconds }
        }

    } catch {
        Write-Host "[ERROR] 타임아웃 캡처 실패: $_"
        return @{
            "Success" = $false
            "Error" = $_.Exception.Message
        }
    }
}

function Test-VelosTimeoutCapture {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS 타임아웃 캡처 테스트 ==="

    # 테스트 시나리오들
    $testScenarios = @(
        @{
            "Name" = "빠른 실행 테스트"
            "Command" = "print('빠른 실행 완료')"
            "Timeout" = 10
        },
        @{
            "Name" = "타임아웃 테스트"
            "Command" = "import time; print('시작'); time.sleep(999); print('끝')"
            "Timeout" = 5
        },
        @{
            "Name" = "한글 출력 테스트"
            "Command" = "print('안녕하세요'); import sys; print('한글 에러', file=sys.stderr)"
            "Timeout" = 10
        }
    )

    foreach ($test in $testScenarios) {
        Write-Host "`n--- $($test.Name) ---"
        $result = Invoke-VelosTimeoutCapture -LogDir $LogDir -Command $test.Command -TimeoutSec $test.Timeout -Prefix "test" -KeepFiles -ShowContent:$false

        if ($result.Success) {
            Write-Host "✓ $($test.Name) 성공"
            Write-Host "  Exit Code: $($result.ExitCode)"
            Write-Host "  STDOUT 크기: $($result.StdoutSize) 바이트"
            Write-Host "  STDERR 크기: $($result.StderrSize) 바이트"
            Write-Host "  타임아웃: $($result.TimedOut)"
            Write-Host "  소요시간: $([math]::Round($result.Duration, 2)) 초"
        } else {
            Write-Host "✗ $($test.Name) 실패: $($result.Error)"
        }
    }
}

# 메인 실행
$result = Invoke-VelosTimeoutCapture -LogDir $LogDir -Command $Command -TimeoutSec $TimeoutSec -Prefix $Prefix -Verbose:$Verbose -KeepFiles:$KeepFiles -ShowContent:$ShowContent

if ($result.Success) {
    Write-Host "`n[SUCCESS] VELOS 타임아웃 캡처 완료"
    Write-Host "타임스탬프: $($result.Timestamp)"
    Write-Host "종료 코드: $($result.ExitCode)"
    Write-Host "타임아웃 발생: $($result.TimedOut)"
    Write-Host "소요시간: $([math]::Round($result.Duration, 2)) 초"
} else {
    Write-Host "`n[FAILED] VELOS 타임아웃 캡처 실패: $($result.Error)"
}

Write-Host "`n=== VELOS 타임아웃 캡처 완료 ==="
