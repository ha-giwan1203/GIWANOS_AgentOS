# [ACTIVE] VELOS 작업 큐 삽입 시스템 - 작업 큐 삽입 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 작업 큐 삽입 스크립트
# VELOS 데이터베이스에 작업을 큐에 삽입하는 기능

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [string]$Task = "테스트 입력",

    [string]$Message = "테스트 알림",

    [string]$Period = "weekly",

    [int]$DecidePriority = 10,

    [int]$ReportPriority = 100,

    [int]$NotifyPriority = 100,

    [int]$TimeoutSec = 20,

    [string]$Tag = "enqueue",

    [switch]$Verbose = $false,

    [switch]$KeepFiles = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Invoke-VelosPy {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Code,

        [int]$TimeoutSec = 45,

        [string]$Tag = "run",

        [string]$LogDir = "C:\giwanos\data\logs",

        [switch]$Verbose = $false,

        [switch]$KeepFiles = $false
    )

    Write-Host "=== VELOS Python 실행 함수 ==="
    Write-Host "태그: $Tag"
    Write-Host "타임아웃: $TimeoutSec 초"

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
        $out = Join-Path $LogDir "$Tag`_$ts.out.txt"
        $err = Join-Path $LogDir "$Tag`_$ts.err.txt"

        Write-Host "[FILES] STDOUT=$out"
        Write-Host "[FILES] STDERR=$err"

        if ($Verbose) {
            Write-Host "`n=== 실행할 Python 코드 ==="
            Write-Host $Code
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
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        $null = $p.Start()

        Write-Host "[PROCESS] 프로세스 시작됨 (PID: $($p.Id))"

        # 코드 주입
        Write-Host "[INPUT] Python 코드 주입 중..."
        $p.StandardInput.Write($Code)
        $p.StandardInput.Close()
        Write-Host "[INPUT] 코드 주입 완료"

        # 타임아웃 감시
        Write-Host "[TIMEOUT] 타임아웃 감시 시작 ($TimeoutSec 초)..."
        $startTime = Get-Date
        $timedOut = $false

        if (-not $p.WaitForExit($TimeoutSec * 1000)) {
            $timedOut = $true
            Write-Host "[TIMEOUT] 타임아웃 발생! 프로세스 종료 중..."
            try {
                $p.Kill($true)
                Write-Host "[TIMEOUT] 프로세스 강제 종료됨 (PID: $($p.Id))"
            } catch {
                Write-Host "[ERROR] 프로세스 종료 실패: $_"
            }

            # 타임아웃 메시지를 stderr에 기록
            $timeoutMsg = "TIMEOUT $TimeoutSec sec"
            $timeoutMsg | Out-File -FilePath $err -Encoding UTF8
            Write-Host "[TIMEOUT] $timeoutMsg"
        } else {
            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds
            Write-Host "[SUCCESS] 프로세스 정상 종료 (소요시간: $([math]::Round($duration, 2)) 초)"
        }

        # 표준출력/에러 파일로 저장
        $p.StandardOutput.ReadToEnd() | Out-File -FilePath $out -Encoding UTF8
        $p.StandardError.ReadToEnd() | Out-File -FilePath $err -Append -Encoding UTF8

        # 파일 크기 확인
        $outSize = if (Test-Path $out) { (Get-Item $out).Length } else { 0 }
        $errSize = if (Test-Path $err) { (Get-Item $err).Length } else { 0 }

        Write-Host "`n=== 파일 정보 ==="
        Write-Host "STDOUT 크기: $outSize 바이트"
        Write-Host "STDERR 크기: $errSize 바이트"
        Write-Host "타임아웃 발생: $timedOut"

        # 파일 내용 표시
        if (Test-Path $out -and $outSize -gt 0) {
            Write-Host "`n=== STDOUT 내용 ==="
            $outContent = Get-Content $out -Raw
            Write-Host $outContent
            Write-Host "=== STDOUT 끝 ==="
        } else {
            Write-Host "`n[INFO] STDOUT 파일이 비어있거나 존재하지 않습니다"
        }

        if (Test-Path $err -and $errSize -gt 0) {
            Write-Host "`n=== STDERR 내용 ==="
            $errContent = Get-Content $err -Raw
            Write-Host $errContent
            Write-Host "=== STDERR 끝 ==="
        } else {
            Write-Host "`n[INFO] STDERR 파일이 비어있거나 존재하지 않습니다"
        }

        # 파일 정리
        if (-not $KeepFiles) {
            Write-Host "`n[CLEANUP] 임시 파일 정리 중..."
            if (Test-Path $out) { Remove-Item $out -Force }
            if (Test-Path $err) { Remove-Item $err -Force }
            Write-Host "[CLEANUP] 임시 파일 삭제 완료"
        } else {
            Write-Host "`n[KEEP] 로그 파일 보존됨:"
            Write-Host "  STDOUT: $out"
            Write-Host "  STDERR: $err"
        }

        # 결과 반환
        $result = @{
            "Success" = $true
            "ExitCode" = $p.ExitCode
            "StdoutFile" = $out
            "StderrFile" = $err
            "StdoutSize" = $outSize
            "StderrSize" = $errSize
            "Timestamp" = $ts
            "TimedOut" = $timedOut
            "ProcessId" = $p.Id
            "Duration" = if ($timedOut) { $TimeoutSec } else { ($endTime - $startTime).TotalSeconds }
        }

        Write-Host "`n[SUCCESS] VELOS Python 실행 완료"
        Write-Host "OK: $out"
        Write-Host "ERR: $err"

        return $result

    } catch {
        Write-Host "[ERROR] VELOS Python 실행 실패: $_"
        $errorMsg = $_.Exception.Message
        $errorMsg | Out-File -FilePath $err -Encoding UTF8
        Write-Host "ERR: $err"

        return @{
            "Success" = $false
            "Error" = $errorMsg
            "StderrFile" = $err
        }
    }
}

function Add-VelosJobs {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [string]$Task = "테스트 입력",
        [string]$Message = "테스트 알림",
        [string]$Period = "weekly",
        [int]$DecidePriority = 10,
        [int]$ReportPriority = 100,
        [int]$NotifyPriority = 100,
        [int]$TimeoutSec = 20,
        [string]$Tag = "enqueue",
        [switch]$Verbose = $false,
        [switch]$KeepFiles = $false
    )

    Write-Host "=== VELOS 작업 큐 삽입 ==="
    Write-Host "태스크: $Task"
    Write-Host "메시지: $Message"
    Write-Host "기간: $Period"
    Write-Host "우선순위: decide=$DecidePriority, report=$ReportPriority, notify=$NotifyPriority"

    # 작업 큐 삽입 코드
    $enqueueCode = @"
import os, sqlite3, json
db=os.getenv("VELOS_DB","C:\\giwanos\\velos.db")
con=sqlite3.connect(db); cur=con.cursor()

# decide 작업 삽입
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("decide", json.dumps({"task":"$Task","notify":True}, ensure_ascii=False), $DecidePriority))

# report 작업 삽입
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("report", json.dumps({"period":"$Period"}, ensure_ascii=False), $ReportPriority))

# notify 작업 삽입
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("notify", json.dumps({"msg":"$Message"}, ensure_ascii=False), $NotifyPriority))

con.commit(); con.close()
print("[OK] queued decide/report/notify")
print(f"  - decide: {{'task': '$Task', 'notify': True}} (priority: $DecidePriority)")
print(f"  - report: {{'period': '$Period'}} (priority: $ReportPriority)")
print(f"  - notify: {{'msg': '$Message'}} (priority: $NotifyPriority)")
"@

    $result = Invoke-VelosPy -Code $enqueueCode -TimeoutSec $TimeoutSec -Tag $Tag -LogDir $LogDir -Verbose:$Verbose -KeepFiles:$KeepFiles

    if ($result.Success) {
        Write-Host "✓ VELOS 작업 큐 삽입 성공"
        Write-Host "삽입된 작업:"
        Write-Host "  - decide: {'task': '$Task', 'notify': True} (priority: $DecidePriority)"
        Write-Host "  - report: {'period': '$Period'} (priority: $ReportPriority)"
        Write-Host "  - notify: {'msg': '$Message'} (priority: $NotifyPriority)"
    } else {
        Write-Host "✗ VELOS 작업 큐 삽입 실패: $($result.Error)"
    }

    return $result
}

function Test-VelosEnqueue {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS 작업 큐 삽입 테스트 ==="

    # 테스트 시나리오들
    $testScenarios = @(
        @{
            "Name" = "기본 작업 삽입"
            "Task" = "기본 테스트 태스크"
            "Message" = "기본 테스트 메시지"
            "Period" = "daily"
            "DecidePriority" = 5
            "ReportPriority" = 50
            "NotifyPriority" = 50
        },
        @{
            "Name" = "한글 작업 삽입"
            "Task" = "한글 테스트 태스크"
            "Message" = "한글 테스트 알림 메시지"
            "Period" = "weekly"
            "DecidePriority" = 10
            "ReportPriority" = 100
            "NotifyPriority" = 100
        },
        @{
            "Name" = "높은 우선순위 작업"
            "Task" = "긴급 태스크"
            "Message" = "긴급 알림"
            "Period" = "monthly"
            "DecidePriority" = 1
            "ReportPriority" = 10
            "NotifyPriority" = 10
        }
    )

    foreach ($test in $testScenarios) {
        Write-Host "`n--- $($test.Name) ---"
        $result = Add-VelosJobs -LogDir $LogDir -Task $test.Task -Message $test.Message -Period $test.Period -DecidePriority $test.DecidePriority -ReportPriority $test.ReportPriority -NotifyPriority $test.NotifyPriority -Tag "test_enqueue" -KeepFiles -Verbose:$false

        if ($result.Success) {
            Write-Host "✓ $($test.Name) 성공"
            Write-Host "  Exit Code: $($result.ExitCode)"
            Write-Host "  STDOUT 크기: $($result.StdoutSize) 바이트"
            Write-Host "  STDERR 크기: $($result.StderrSize) 바이트"
            Write-Host "  소요시간: $([math]::Round($result.Duration, 2)) 초"
        } else {
            Write-Host "✗ $($test.Name) 실패: $($result.Error)"
        }
    }
}

# 메인 실행
$result = Add-VelosJobs -LogDir $LogDir -Task $Task -Message $Message -Period $Period -DecidePriority $DecidePriority -ReportPriority $ReportPriority -NotifyPriority $NotifyPriority -TimeoutSec $TimeoutSec -Tag $Tag -Verbose:$Verbose -KeepFiles:$KeepFiles

if ($result.Success) {
    Write-Host "`n[SUCCESS] VELOS 작업 큐 삽입 완료"
    Write-Host "타임스탬프: $($result.Timestamp)"
    Write-Host "종료 코드: $($result.ExitCode)"
    Write-Host "소요시간: $([math]::Round($result.Duration, 2)) 초"
} else {
    Write-Host "`n[FAILED] VELOS 작업 큐 삽입 실패: $($result.Error)"
}

Write-Host "`n=== VELOS 작업 큐 삽입 완료 ==="



