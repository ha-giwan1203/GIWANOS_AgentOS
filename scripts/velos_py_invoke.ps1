# [ACTIVE] VELOS Python 실행 함수 시스템 - Python 코드 실행 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Python 실행 함수 스크립트
# 재사용 가능한 Python 실행 함수 및 스키마 초기화 기능

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [string]$Code = "",

    [int]$TimeoutSec = 45,

    [string]$Tag = "run",

    [switch]$Verbose = $false,

    [switch]$KeepFiles = $false,

    [switch]$ShowContent = $true,

    [switch]$InitSchema = $false
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

        [switch]$KeepFiles = $false,

        [switch]$ShowContent = $true
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
        if ($ShowContent) {
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

function Initialize-VelosSchema {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",

        [int]$TimeoutSec = 20,

        [switch]$Verbose = $false,

        [switch]$KeepFiles = $false
    )

    Write-Host "=== VELOS 스키마 초기화 ==="

    # 스키마 초기화 코드
    $schemaCode = @'
import os, sqlite3
db=os.getenv("VELOS_DB","C:\\giwanos\\velos.db")
con=sqlite3.connect(db); cur=con.cursor()

# job_queue 테이블 생성
cur.execute("""CREATE TABLE IF NOT EXISTS job_queue(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  priority INTEGER NOT NULL DEFAULT 100,
  heartbeat INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
)""")

# 기타 필요한 테이블들 추가
cur.execute("""CREATE TABLE IF NOT EXISTS system_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS execution_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER,
  status TEXT NOT NULL,
  output TEXT,
  error TEXT,
  duration REAL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (job_id) REFERENCES job_queue (id)
)""")

con.commit(); con.close()
print("VELOS 스키마 초기화 완료")
print("생성된 테이블:")
print("- job_queue: 작업 큐 관리")
print("- system_log: 시스템 로그")
print("- execution_history: 실행 이력")
'@

    $result = Invoke-VelosPy -Code $schemaCode -TimeoutSec $TimeoutSec -Tag "schema" -LogDir $LogDir -Verbose:$Verbose -KeepFiles:$KeepFiles

    if ($result.Success) {
        Write-Host "✓ VELOS 스키마 초기화 성공"
    } else {
        Write-Host "✗ VELOS 스키마 초기화 실패: $($result.Error)"
    }

    return $result
}

function Test-VelosPyInvoke {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS Python 실행 함수 테스트 ==="

    # 테스트 시나리오들
    $testScenarios = @(
        @{
            "Name" = "기본 출력 테스트"
            "Code" = "print('Hello, VELOS!')"
            "Tag" = "test_basic"
            "Timeout" = 10
        },
        @{
            "Name" = "한글 출력 테스트"
            "Code" = "print('안녕하세요, VELOS!'); import sys; print('한글 에러 테스트', file=sys.stderr)"
            "Tag" = "test_korean"
            "Timeout" = 10
        },
        @{
            "Name" = "타임아웃 테스트"
            "Code" = "import time; print('시작'); time.sleep(999); print('끝')"
            "Tag" = "test_timeout"
            "Timeout" = 5
        },
        @{
            "Name" = "데이터베이스 테스트"
            "Code" = @'
import os, sqlite3
db=os.getenv('VELOS_DB','C:\\giwanos\\velos.db')
con=sqlite3.connect(db)
cur=con.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cur.fetchall()
print('테이블 목록:')
for table in tables:
    print(f'- {table[0]}')
con.close()
'@
            "Tag" = "test_db"
            "Timeout" = 15
        }
    )

    foreach ($test in $testScenarios) {
        Write-Host "`n--- $($test.Name) ---"
        $result = Invoke-VelosPy -Code $test.Code -TimeoutSec $test.Timeout -Tag $test.Tag -LogDir $LogDir -KeepFiles -ShowContent:$false

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
if ($InitSchema) {
    # 스키마 초기화 실행
    Initialize-VelosSchema -LogDir $LogDir -TimeoutSec $TimeoutSec -Verbose:$Verbose -KeepFiles:$KeepFiles
} elseif ($Code) {
    # 사용자 코드 실행
    $result = Invoke-VelosPy -Code $Code -TimeoutSec $TimeoutSec -Tag $Tag -LogDir $LogDir -Verbose:$Verbose -KeepFiles:$KeepFiles -ShowContent:$ShowContent

    if ($result.Success) {
        Write-Host "`n[SUCCESS] VELOS Python 실행 완료"
        Write-Host "타임스탬프: $($result.Timestamp)"
        Write-Host "종료 코드: $($result.ExitCode)"
        Write-Host "타임아웃 발생: $($result.TimedOut)"
        Write-Host "소요시간: $([math]::Round($result.Duration, 2)) 초"
    } else {
        Write-Host "`n[FAILED] VELOS Python 실행 실패: $($result.Error)"
    }
} else {
    # 테스트 실행
    Test-VelosPyInvoke -LogDir $LogDir
}

Write-Host "`n=== VELOS Python 실행 함수 완료 ==="
