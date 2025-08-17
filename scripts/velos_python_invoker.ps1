# VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# 환경 변수에서 VELOS_ROOT 경로 로드
$velosRoot = $env:VELOS_ROOT
if (-not $velosRoot) {
    # 기본값으로 C:\giwanos 사용
    $velosRoot = "C:\giwanos"
}

# 로그 디렉토리 경로 설정
$logDir = Join-Path $velosRoot "data\logs"

# 로그 디렉토리 존재 확인 및 생성
if (!(Test-Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "로그 디렉토리가 생성되었습니다: $logDir" -ForegroundColor Green
    }
    catch {
        Write-Error "로그 디렉토리 생성 실패: $($_.Exception.Message)"
        exit 1
    }
}

function Invoke-VelosPy {
    param(
        [Parameter(Mandatory=$true)][string]$Code,
        [int]$TimeoutSec = 45,
        [string]$Tag = "run"
    )

    Write-Host "VELOS Python 실행 시작 (태그: $Tag, 타임아웃: ${TimeoutSec}초)" -ForegroundColor Cyan

    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $out = Join-Path $logDir "$Tag`_$ts.out.txt"
    $err = Join-Path $logDir "$Tag`_$ts.err.txt"

    try {
        # ProcessStartInfo 설정
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

        Write-Host "프로세스 시작됨 (PID: $($p.Id))" -ForegroundColor Green

        # 코드 주입
        $p.StandardInput.Write($Code)
        $p.StandardInput.Close()

        Write-Host "Python 코드 주입 완료" -ForegroundColor Green

        # 타임아웃 감시 및 대기
        if (-not $p.WaitForExit($TimeoutSec * 1000)) {
            try {
                $p.Kill($true)
                Write-Host "타임아웃 발생 - 프로세스 종료됨 (PID: $($p.Id))" -ForegroundColor Red
            } catch {
                Write-Warning "프로세스 종료 중 오류: $($_.Exception.Message)"
            }
            "TIMEOUT $TimeoutSec sec" | Out-File -FilePath $err -Encoding UTF8
        } else {
            Write-Host "프로세스 정상 종료됨 (종료 코드: $($p.ExitCode))" -ForegroundColor Green
        }

        # 표준출력/에러 파일로 저장
        $p.StandardOutput.ReadToEnd() | Out-File -FilePath $out -Encoding UTF8
        $p.StandardError.ReadToEnd() | Out-File -FilePath $err -Append -Encoding UTF8

        # 자가 검증: 출력 파일 존재 확인
        if (Test-Path $out) {
            Write-Host "STDOUT=$out" -ForegroundColor Cyan
            Write-Host "=== STDOUT 내용 ===" -ForegroundColor Yellow
            Get-Content $out -Raw
        } else {
            Write-Warning "STDOUT 파일이 생성되지 않았습니다: $out"
        }

        if (Test-Path $err) {
            Write-Host "STDERR=$err" -ForegroundColor Cyan
            Write-Host "=== STDERR 내용 ===" -ForegroundColor Red
            Get-Content $err -Raw
        } else {
            Write-Warning "STDERR 파일이 생성되지 않았습니다: $err"
        }

        # 실행 결과 요약
        $outSize = if (Test-Path $out) { (Get-Item $out).Length } else { 0 }
        $errSize = if (Test-Path $err) { (Get-Item $err).Length } else { 0 }

        Write-Host "실행 완료 - STDOUT: ${outSize}바이트, STDERR: ${errSize}바이트" -ForegroundColor Green

        "OK: $out`nERR: $err"

    } catch {
        Write-Error "Python 프로세스 실행 실패: $($_.Exception.Message)"
        $_ | Out-File -FilePath $err -Encoding UTF8
        "ERR: $err"
    }
}

# 스키마 초기화 코드
$schemaCode = @'
import os, sqlite3
db=os.getenv("VELOS_DB","C:\\giwanos\\velos.db")
con=sqlite3.connect(db); cur=con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS job_queue(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  priority INTEGER NOT NULL DEFAULT 100,
  heartbeat INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
)""")
con.commit(); con.close()
print("schema ok")
'@

Write-Host "VELOS 스키마 초기화 시작..." -ForegroundColor Magenta
$result = Invoke-VelosPy -Code $schemaCode -TimeoutSec 20 -Tag "schema"
Write-Host "스키마 초기화 결과: $result" -ForegroundColor Magenta
