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
    VELOS 마스터 스케줄러 Windows Task Scheduler 등록
.DESCRIPTION
    VELOS 마스터 스케줄러를 Windows Task Scheduler에 등록하여 5분마다 자동 실행되도록 설정합니다.
    VELOS 운영 철학에 따라 안전하고 견고한 스케줄링을 보장합니다.
.PARAMETER Remove
    기존 태스크 제거
.PARAMETER WhatIf
    실제 등록 없이 미리보기
.EXAMPLE
    .\create_velos_master_scheduler_task.ps1
.EXAMPLE
    .\create_velos_master_scheduler_task.ps1 -Remove
.EXAMPLE
    .\create_velos_master_scheduler_task.ps1 -WhatIf
#>

param(
    [switch]$Remove,
    [switch]$WhatIf
)

# 관리자 권한 확인
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "관리자 권한이 필요합니다. PowerShell을 관리자 권한으로 실행해주세요." -ForegroundColor Red
    exit 1
}

# VELOS 환경 설정
$VELOS_ROOT = $env:VELOS_ROOT
if (-not $VELOS_ROOT) {
    $VELOS_ROOT = "C:\giwanos"
}

# 태스크 설정
$TASK_NAME = "VELOS-MasterLoop"
$TASK_DESCRIPTION = "VELOS 마스터 스케줄러 - 5분마다 실행되어 모든 VELOS 작업을 관리"
$VBS_PATH = Join-Path $VELOS_ROOT "scripts\Start-Velos-Hidden.vbs"

# 로그 디렉토리
$LOG_DIR = Join-Path $VELOS_ROOT "data\logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

function Write-VelosLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    $logFile = Join-Path $LOG_DIR "task_creation.log"
    Add-Content -Path $logFile -Value $logEntry -Encoding UTF8
    
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
}

function Test-VelosPrerequisites {
    """VELOS 전제 조건 검증"""
    try {
        Write-VelosLog "VELOS 전제 조건 검증 중..."
        
        # VELOS 루트 경로 확인
        if (-not (Test-Path $VELOS_ROOT)) {
            throw "VELOS_ROOT not found: $VELOS_ROOT"
        }
        
        # VBScript 확인
        if (-not (Test-Path $VBS_PATH)) {
            throw "VBScript not found: $VBS_PATH"
        }
        
        # 마스터 스케줄러 파일 확인
        $masterSchedulerPath = Join-Path $VELOS_ROOT "scripts\run_giwanos_master_loop.py"
        if (-not (Test-Path $masterSchedulerPath)) {
            throw "Master scheduler not found: $masterSchedulerPath"
        }
        
        # VBScript 파일 확인
        $vbsPath = Join-Path $VELOS_ROOT "scripts\Start-Velos-Hidden.vbs"
        if (-not (Test-Path $vbsPath)) {
            throw "VBScript not found: $vbsPath"
        }
        
        # PowerShell 실행 정책 확인
        $executionPolicy = Get-ExecutionPolicy
        if ($executionPolicy -eq "Restricted") {
            Write-VelosLog "PowerShell execution policy is Restricted. Consider setting to RemoteSigned." "WARN"
        }
        
        Write-VelosLog "VELOS 전제 조건 검증 완료" "SUCCESS"
        return $true
    }
    catch {
        Write-VelosLog "전제 조건 검증 실패: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Remove-VelosTask {
    """기존 VELOS 태스크 제거"""
    try {
        Write-VelosLog "기존 VELOS 태스크 제거 중..."
        
        $taskExists = schtasks /query /tn $TASK_NAME 2>$null
        if ($LASTEXITCODE -eq 0) {
            if ($WhatIf) {
                Write-VelosLog "Would remove task: $TASK_NAME" "WARN"
                return $true
            }
            
            schtasks /delete /tn $TASK_NAME /f 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-VelosLog "기존 태스크 제거 완료: $TASK_NAME" "SUCCESS"
                return $true
            }
            else {
                Write-VelosLog "태스크 제거 실패: $TASK_NAME" "ERROR"
                return $false
            }
        }
        else {
            Write-VelosLog "기존 태스크가 존재하지 않음: $TASK_NAME"
            return $true
        }
    }
    catch {
        Write-VelosLog "태스크 제거 중 오류: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Create-VelosTask {
    """VELOS 태스크 생성"""
    try {
        Write-VelosLog "VELOS 태스크 생성 중..."
        
        if ($WhatIf) {
            Write-VelosLog "Would create task: $TASK_NAME" "WARN"
            Write-VelosLog "  VBScript: $VBS_PATH" "WARN"
            Write-VelosLog "  Schedule: Every 5 minutes" "WARN"
            return $true
        }
        
        # VBScript를 통한 숨겨진 실행 (더 안정적)
        $vbsCommand = "cscript.exe `"$VBS_PATH`""
        
        # 태스크 생성 명령
        $createCommand = @"
schtasks /create /tn "$TASK_NAME" /tr "$vbsCommand" /sc minute /mo 5 /ru "SYSTEM" /f /rl highest
"@
        
        Write-VelosLog "태스크 생성 명령 실행: $createCommand"
        
        # 태스크 생성
        $result = Invoke-Expression $createCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-VelosLog "VELOS 태스크 생성 완료: $TASK_NAME" "SUCCESS"
            
            # 태스크 설정 확인
            $taskInfo = schtasks /query /tn $TASK_NAME /fo csv 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-VelosLog "태스크 정보:"
                $taskInfo | ForEach-Object { Write-VelosLog "  $_" }
            }
            
            return $true
        }
        else {
            Write-VelosLog "태스크 생성 실패: $result" "ERROR"
            return $false
        }
    }
    catch {
        Write-VelosLog "태스크 생성 중 오류: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-VelosTask {
    """생성된 태스크 테스트"""
    try {
        Write-VelosLog "VELOS 태스크 테스트 중..."
        
        if ($WhatIf) {
            Write-VelosLog "Would test task: $TASK_NAME" "WARN"
            return $true
        }
        
        # 태스크 존재 확인
        $taskExists = schtasks /query /tn $TASK_NAME 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-VelosLog "태스크가 존재하지 않음: $TASK_NAME" "ERROR"
            return $false
        }
        
        # 태스크 상태 확인
        $taskStatus = schtasks /query /tn $TASK_NAME /fo csv 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-VelosLog "태스크 상태 확인 완료" "SUCCESS"
            $taskStatus | ForEach-Object { Write-VelosLog "  $_" }
            return $true
        }
        else {
            Write-VelosLog "태스크 상태 확인 실패" "ERROR"
            return $false
        }
    }
    catch {
        Write-VelosLog "태스크 테스트 중 오류: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# 메인 실행 로직
try {
    Write-VelosLog "VELOS 마스터 스케줄러 태스크 관리 시작"
    Write-VelosLog "VELOS_ROOT: $VELOS_ROOT"
    Write-VelosLog "Script Path: $SCRIPT_PATH"
    
    if ($WhatIf) {
        Write-VelosLog "WhatIf 모드 - 실제 변경 없이 미리보기" "WARN"
    }
    
    # 전제 조건 검증
    if (-not (Test-VelosPrerequisites)) {
        exit 1
    }
    
    if ($Remove) {
        # 기존 태스크 제거
        if (-not (Remove-VelosTask)) {
            exit 1
        }
        Write-VelosLog "VELOS 태스크 제거 완료" "SUCCESS"
    }
    else {
        # 기존 태스크 제거 후 새로 생성
        if (-not (Remove-VelosTask)) {
            exit 1
        }
        
        # 새 태스크 생성
        if (-not (Create-VelosTask)) {
            exit 1
        }
        
        # 태스크 테스트
        if (-not (Test-VelosTask)) {
            exit 1
        }
        
        Write-VelosLog "VELOS 마스터 스케줄러 태스크 등록 완료" "SUCCESS"
        Write-VelosLog "태스크는 5분마다 자동으로 실행됩니다." "SUCCESS"
    }
    
    exit 0
}
catch {
    Write-VelosLog "치명적 오류: $($_.Exception.Message)" "ERROR"
    exit 1
}
