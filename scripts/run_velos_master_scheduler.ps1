# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
<#
.SYNOPSIS
    VELOS 마스터 스케줄러 실행 스크립트
.DESCRIPTION
    Windows Task Scheduler에서 5분마다 실행되어 VELOS 마스터 스케줄러를 호출합니다.
    VELOS 운영 철학에 따라 안전하고 견고한 실행을 보장합니다.
.PARAMETER DryRun
    실제 실행 없이 테스트만 수행
.PARAMETER Verbose
    상세 로그 출력
.EXAMPLE
    .\run_velos_master_scheduler.ps1
.EXAMPLE
    .\run_velos_master_scheduler.ps1 -DryRun -Verbose
#>

param(
    [switch]$DryRun,
    [switch]$Verbose
)

# 오류 처리 설정
$ErrorActionPreference = "Stop"

# VELOS 환경 설정
$VELOS_ROOT = $env:VELOS_ROOT
if (-not $VELOS_ROOT) {
    $VELOS_ROOT = "C:\giwanos"
}

# Python 경로 설정
$PYTHON_PATH = $env:VELOS_PYTHON
if (-not $PYTHON_PATH) {
    $PYTHON_PATH = "python"
}

# 로그 디렉토리
$LOG_DIR = Join-Path $VELOS_ROOT "data\logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# 실행 로그 파일
$EXEC_LOG = Join-Path $LOG_DIR "scheduler_exec.log"

function Write-VelosLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 파일 로그
    Add-Content -Path $EXEC_LOG -Value $logEntry -Encoding UTF8
    
    # 콘솔 출력 (Verbose 모드에서만)
    if ($Verbose) {
        Write-Host $logEntry
    }
}

function Test-VelosEnvironment {
    """VELOS 환경 검증"""
    try {
        # VELOS 루트 경로 확인
        if (-not (Test-Path $VELOS_ROOT)) {
            throw "VELOS_ROOT not found: $VELOS_ROOT"
        }
        
        # Python 실행 가능 확인
        $pythonTest = & $PYTHON_PATH --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Python not available: $pythonTest"
        }
        
        # 마스터 스케줄러 파일 확인
        $schedulerPath = Join-Path $VELOS_ROOT "scripts\velos_master_scheduler.py"
        if (-not (Test-Path $schedulerPath)) {
            throw "Master scheduler not found: $schedulerPath"
        }
        
        Write-VelosLog "VELOS environment validated"
        return $true
    }
    catch {
        Write-VelosLog "Environment validation failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Invoke-VelosScheduler {
    """VELOS 마스터 스케줄러 실행"""
    try {
        $schedulerPath = Join-Path $VELOS_ROOT "scripts\velos_master_scheduler.py"
        
        # 실행 인자 구성
        $args = @()
        if ($DryRun) {
            $args += "--dry-run"
        }
        if ($Verbose) {
            $args += "--verbose"
        }
        
        Write-VelosLog "Starting VELOS master scheduler with args: $($args -join ' ')"
        
        # Python 환경 변수 설정
        $env:PYTHONPATH = "$VELOS_ROOT;$VELOS_ROOT\modules"
        $env:VELOS_ROOT = $VELOS_ROOT
        
        # 스케줄러 실행
        $result = & $PYTHON_PATH $schedulerPath @args 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-VelosLog "VELOS scheduler completed successfully"
            if ($Verbose -and $result) {
                $result | ForEach-Object { Write-VelosLog "  $_" }
            }
            return $true
        }
        else {
            Write-VelosLog "VELOS scheduler failed with exit code: $LASTEXITCODE" "ERROR"
            if ($result) {
                $result | ForEach-Object { Write-VelosLog "  $_" "ERROR" }
            }
            return $false
        }
    }
    catch {
        Write-VelosLog "Scheduler execution exception: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# 메인 실행 로직
try {
    Write-VelosLog "VELOS Master Scheduler started"
    Write-VelosLog "VELOS_ROOT: $VELOS_ROOT"
    Write-VelosLog "Python: $PYTHON_PATH"
    
    # 환경 검증
    if (-not (Test-VelosEnvironment)) {
        exit 1
    }
    
    # 스케줄러 실행
    if (-not (Invoke-VelosScheduler)) {
        exit 1
    }
    
    Write-VelosLog "VELOS Master Scheduler completed successfully"
    exit 0
}
catch {
    Write-VelosLog "Critical error: $($_.Exception.Message)" "ERROR"
    exit 1
}
finally {
    # 정리 작업
    if ($Verbose) {
        Write-VelosLog "Cleanup completed"
    }
}
