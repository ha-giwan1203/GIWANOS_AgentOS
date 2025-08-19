# [ACTIVE] VELOS 작업 큐 관리 시스템 - 작업 큐 관리 스크립트
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 작업 큐 관리 스크립트
# VELOS 데이터베이스에 작업을 큐에 삽입합니다.

param(
    [string]$JobType = "all",

    [string]$Task = "테스트 입력",

    [string]$Message = "테스트 알림",

    [string]$Period = "weekly",

    [int]$DecidePriority = 10,

    [int]$ReportPriority = 100,

    [int]$NotifyPriority = 100,

    [switch]$Verbose = $false,

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

function Add-VelosJobQueue {
    param(
        [string]$JobType = "all",
        [string]$Task = "테스트 입력",
        [string]$Message = "테스트 알림",
        [string]$Period = "weekly",
        [int]$DecidePriority = 10,
        [int]$ReportPriority = 100,
        [int]$NotifyPriority = 100,
        [switch]$Verbose = $false,
        [switch]$KeepOutput = $false
    )

    $outputFile = "$env:TEMP\velos_job_queue_output.txt"

    Write-Host "=== VELOS 작업 큐 관리 ==="
    Write-Host "작업 유형: $JobType"
    Write-Host "태스크: $Task"
    Write-Host "메시지: $Message"
    Write-Host "기간: $Period"

    try {
        # Python 스크립트 생성
        $pythonScript = @"
import os, sqlite3, json
db=os.getenv("VELOS_DB","C:\\giwanos\\velos.db")
con=sqlite3.connect(db); cur=con.cursor()

# 작업 큐에 작업 삽입
if "$JobType" in ["all", "decide"]:
    cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
                ("decide", json.dumps({"task":"$Task","notify":True}, ensure_ascii=False), $DecidePriority))
    print("[OK] queued decide job")

if "$JobType" in ["all", "report"]:
    cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
                ("report", json.dumps({"period":"$Period"}, ensure_ascii=False), $ReportPriority))
    print("[OK] queued report job")

if "$JobType" in ["all", "notify"]:
    cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
                ("notify", json.dumps({"msg":"$Message"}, ensure_ascii=False), $NotifyPriority))
    print("[OK] queued notify job")

con.commit(); con.close()
print("[SUCCESS] All jobs queued successfully")
"@

        # 임시 Python 파일 생성
        $tempPythonFile = "$env:TEMP\velos_job_queue_temp.py"
        $pythonScript | Out-File -FilePath $tempPythonFile -Encoding UTF8

        Write-Host "[SCRIPT] 임시 Python 스크립트 생성: $tempPythonFile"

        if ($Verbose) {
            Write-Host "`n=== Python 스크립트 내용 ==="
            Write-Host $pythonScript
            Write-Host "=== Python 스크립트 끝 ==="
        }

        # Python 스크립트 실행
        $process = Start-Process -FilePath "python" -ArgumentList $tempPythonFile -RedirectStandardOutput $outputFile -RedirectStandardError "$outputFile.err" -Wait -PassThru -NoNewWindow

        if ($process.ExitCode -eq 0) {
            Write-Host "[SUCCESS] 작업 큐 삽입 완료"

            if (Test-Path $outputFile) {
                $outputContent = Get-Content $outputFile -Raw
                Write-Host "`n=== 실행 결과 ==="
                Write-Host $outputContent
                Write-Host "=== 실행 결과 끝 ==="

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
            Write-Host "[ERROR] 작업 큐 삽입 실패 (Exit Code: $($process.ExitCode))"

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
        Write-Host "[ERROR] 작업 큐 삽입 실패: $_"
    } finally {
        # 정리
        if (Test-Path $tempPythonFile) { Remove-Item $tempPythonFile -Force -ErrorAction SilentlyContinue }
        if (Test-Path $outputFile) {
            if (-not $KeepOutput) { Remove-Item $outputFile -Force -ErrorAction SilentlyContinue }
        }
        if (Test-Path "$outputFile.err") { Remove-Item "$outputFile.err" -Force -ErrorAction SilentlyContinue }
    }
}

# 메인 실행
Add-VelosJobQueue -JobType $JobType -Task $Task -Message $Message -Period $Period -DecidePriority $DecidePriority -ReportPriority $ReportPriority -NotifyPriority $NotifyPriority -Verbose:$Verbose -KeepOutput:$KeepOutput

Write-Host "`n=== VELOS 작업 큐 관리 완료 ==="



