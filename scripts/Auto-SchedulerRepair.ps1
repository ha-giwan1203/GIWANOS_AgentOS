# [ACTIVE] VELOS 스케줄러 자동 복구 시스템
# 문제 발견 시 자동으로 진단하고 수정하는 스마트 복구 도구

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$AutoFix,
    [switch]$ForceRepair,
    [switch]$BackupFirst,
    [switch]$WhatIf,
    [string]$LogPath = "data\logs\auto_repair_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

$ErrorActionPreference = 'Continue'

function Write-RepairLog {
    param([string]$Message, [string]$Level = "INFO", [ConsoleColor]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $Color
    
    # 로그 디렉토리 생성
    $logDir = Split-Path $LogPath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Backup-CurrentScheduler {
    try {
        $backupDir = "data\backups\scheduler_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        # 현재 스케줄드 태스크 백업
        $velosTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*VELOS*" }
        foreach ($task in $velosTasks) {
            $xml = Export-ScheduledTask -TaskName $task.TaskName
            $xmlPath = Join-Path $backupDir "$($task.TaskName).xml"
            $xml | Out-File -FilePath $xmlPath -Encoding UTF8
        }
        
        Write-RepairLog "스케줄러 백업 완료: $backupDir" "SUCCESS" "Green"
        return $backupDir
    } catch {
        Write-RepairLog "백업 실패: $($_.Exception.Message)" "ERROR" "Red"
        return $null
    }
}

function Repair-MissingFiles {
    $repairCount = 0
    
    # 필수 파일 목록
    $requiredFiles = @{
        "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml" = 2000
        "scripts\Invoke-VelosParallel.ps1" = 8000
        "scripts\Start-Velos-CompletelyHidden.vbs" = 3000
        "scripts\Optimize-VelosScheduler.ps1" = 8000
    }
    
    foreach ($file in $requiredFiles.Keys) {
        $expectedSize = $requiredFiles[$file]
        
        if (-not (Test-Path $file)) {
            Write-RepairLog "❌ 누락된 파일 발견: $file" "ERROR" "Red"
            
            if ($AutoFix) {
                Write-RepairLog "Git에서 파일 복구 시도 중..." "INFO" "Yellow"
                if (-not $WhatIf) {
                    try {
                        & git checkout HEAD -- $file 2>$null
                        if (Test-Path $file) {
                            Write-RepairLog "✅ 파일 복구 성공: $file" "SUCCESS" "Green"
                            $repairCount++
                        }
                    } catch {
                        Write-RepairLog "파일 복구 실패: $file" "ERROR" "Red"
                    }
                }
            }
        } elseif ((Get-Item $file).Length -lt $expectedSize) {
            Write-RepairLog "⚠️ 손상된 파일 발견: $file (크기: $((Get-Item $file).Length) < $expectedSize)" "WARN" "Yellow"
            
            if ($AutoFix) {
                Write-RepairLog "손상된 파일 복구 시도 중..." "INFO" "Yellow"
                if (-not $WhatIf) {
                    try {
                        & git checkout HEAD -- $file 2>$null
                        if ((Get-Item $file).Length -ge $expectedSize) {
                            Write-RepairLog "✅ 파일 복구 성공: $file" "SUCCESS" "Green"
                            $repairCount++
                        }
                    } catch {
                        Write-RepairLog "파일 복구 실패: $file" "ERROR" "Red"
                    }
                }
            }
        }
    }
    
    return $repairCount
}

function Repair-DuplicatedTasks {
    $repairCount = 0
    
    try {
        $velosTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*VELOS*" }
        $duplicates = $velosTasks | Group-Object TaskName | Where-Object Count -gt 1
        
        if ($duplicates.Count -gt 0) {
            Write-RepairLog "❌ 중복 태스크 발견: $($duplicates.Count)개 그룹" "ERROR" "Red"
            
            foreach ($group in $duplicates) {
                $tasksToRemove = $group.Group | Sort-Object { 
                    # 우선순위: Hidden > Optimized > 기타
                    if ($_.TaskName -like "*Hidden*") { 0 }
                    elseif ($_.TaskName -like "*Optimized*") { 1 }
                    else { 2 }
                } | Select-Object -Skip 1  # 첫 번째(우선순위 높은) 것만 유지
                
                foreach ($task in $tasksToRemove) {
                    Write-RepairLog "중복 태스크 제거 대상: $($task.TaskName)" "INFO" "Yellow"
                    
                    if ($AutoFix -and -not $WhatIf) {
                        try {
                            Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                            Write-RepairLog "✅ 중복 태스크 제거 완료: $($task.TaskName)" "SUCCESS" "Green"
                            $repairCount++
                        } catch {
                            Write-RepairLog "중복 태스크 제거 실패: $($task.TaskName) - $($_.Exception.Message)" "ERROR" "Red"
                        }
                    }
                }
            }
        }
    } catch {
        Write-RepairLog "중복 태스크 검사 실패: $($_.Exception.Message)" "ERROR" "Red"
    }
    
    return $repairCount
}

function Repair-DisabledTasks {
    $repairCount = 0
    
    try {
        $velosTasks = Get-ScheduledTask | Where-Object { 
            $_.TaskName -like "*VELOS*" -and $_.State -eq 'Disabled' 
        }
        
        foreach ($task in $velosTasks) {
            Write-RepairLog "❌ 비활성화된 태스크 발견: $($task.TaskName)" "ERROR" "Red"
            
            if ($AutoFix -and -not $WhatIf) {
                try {
                    Enable-ScheduledTask -TaskName $task.TaskName
                    Write-RepairLog "✅ 태스크 활성화 완료: $($task.TaskName)" "SUCCESS" "Green"
                    $repairCount++
                } catch {
                    Write-RepairLog "태스크 활성화 실패: $($task.TaskName) - $($_.Exception.Message)" "ERROR" "Red"
                }
            }
        }
    } catch {
        Write-RepairLog "비활성화 태스크 검사 실패: $($_.Exception.Message)" "ERROR" "Red"
    }
    
    return $repairCount
}

function Repair-MissingOptimizedTask {
    try {
        $optimizedTasks = Get-ScheduledTask | Where-Object { 
            $_.TaskName -like "*VELOS*Hidden*" -or $_.TaskName -like "*VELOS*Optimized*" 
        }
        
        if ($optimizedTasks.Count -eq 0) {
            Write-RepairLog "❌ 최적화된 스케줄러 태스크가 없습니다" "ERROR" "Red"
            
            if ($AutoFix) {
                Write-RepairLog "최적화된 스케줄러 설치 시도 중..." "INFO" "Yellow"
                
                if (-not $WhatIf) {
                    $xmlPath = "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml"
                    if (Test-Path $xmlPath) {
                        try {
                            Register-ScheduledTask -Xml (Get-Content $xmlPath | Out-String) -TaskName "VELOS Master Scheduler Hidden" -Force
                            Write-RepairLog "✅ 최적화된 스케줄러 설치 완료" "SUCCESS" "Green"
                            return 1
                        } catch {
                            Write-RepairLog "최적화된 스케줄러 설치 실패: $($_.Exception.Message)" "ERROR" "Red"
                        }
                    } else {
                        Write-RepairLog "XML 파일을 찾을 수 없음: $xmlPath" "ERROR" "Red"
                    }
                }
            }
        } else {
            Write-RepairLog "✅ 최적화된 스케줄러 태스크 존재: $($optimizedTasks.Count)개" "SUCCESS" "Green"
        }
    } catch {
        Write-RepairLog "최적화 태스크 검사 실패: $($_.Exception.Message)" "ERROR" "Red"
    }
    
    return 0
}

function Create-MissingDirectories {
    $repairCount = 0
    $requiredDirs = @("data\logs", "data\reports", "data\sessions", "data\backups")
    
    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            Write-RepairLog "❌ 누락된 디렉토리: $dir" "ERROR" "Red"
            
            if ($AutoFix -and -not $WhatIf) {
                try {
                    New-Item -ItemType Directory -Path $dir -Force | Out-Null
                    Write-RepairLog "✅ 디렉토리 생성 완료: $dir" "SUCCESS" "Green"
                    $repairCount++
                } catch {
                    Write-RepairLog "디렉토리 생성 실패: $dir - $($_.Exception.Message)" "ERROR" "Red"
                }
            }
        }
    }
    
    return $repairCount
}

# 메인 실행
Clear-Host
Write-Host "🔧 VELOS 스케줄러 자동 복구 시스템" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-RepairLog "자동 복구 시작" "INFO" "White"

# 관리자 권한 확인
$isAdmin = Test-AdminPrivileges
if (-not $isAdmin) {
    Write-RepairLog "❌ 관리자 권한이 필요합니다" "ERROR" "Red"
    Write-Host "PowerShell을 관리자 권한으로 재실행해주세요." -ForegroundColor Red
    exit 1
}

# 백업 생성
$backupPath = $null
if ($BackupFirst -and $AutoFix -and -not $WhatIf) {
    Write-RepairLog "📦 현재 상태 백업 중..." "INFO" "Yellow"
    $backupPath = Backup-CurrentScheduler
}

# 복구 작업 시작
Write-RepairLog "`n🔍 문제 진단 및 복구 시작..." "INFO" "Yellow"

$totalRepairs = 0

# 1. 필수 파일 복구
Write-RepairLog "`n📁 1단계: 파일 시스템 복구" "INFO" "Cyan"
$totalRepairs += Repair-MissingFiles

# 2. 디렉토리 생성
Write-RepairLog "`n📂 2단계: 디렉토리 구조 복구" "INFO" "Cyan"
$totalRepairs += Create-MissingDirectories

if ($isAdmin) {
    # 3. 중복 태스크 정리
    Write-RepairLog "`n🗑️ 3단계: 중복 태스크 정리" "INFO" "Cyan"
    $totalRepairs += Repair-DuplicatedTasks
    
    # 4. 비활성화 태스크 활성화
    Write-RepairLog "`n⚡ 4단계: 비활성화 태스크 복구" "INFO" "Cyan"
    $totalRepairs += Repair-DisabledTasks
    
    # 5. 최적화된 태스크 설치
    Write-RepairLog "`n🚀 5단계: 최적화 태스크 설치" "INFO" "Cyan"
    $totalRepairs += Repair-MissingOptimizedTask
}

# 최종 결과
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-RepairLog "🎯 자동 복구 완료" "INFO" "White"

if ($WhatIf) {
    Write-RepairLog "📋 WhatIf 모드 - 실제 수정 없음" "INFO" "Cyan"
    Write-RepairLog "실제 복구를 위해 -AutoFix 매개변수 사용" "INFO" "Cyan"
} else {
    Write-RepairLog "총 복구된 항목: $totalRepairs개" "SUCCESS" "Green"
    
    if ($totalRepairs -gt 0) {
        Write-RepairLog "✅ 복구 작업이 완료되었습니다!" "SUCCESS" "Green"
        if ($backupPath) {
            Write-RepairLog "백업 위치: $backupPath" "INFO" "Gray"
        }
        Write-RepairLog "상태 확인: .\scripts\Quick-SchedulerStatus.ps1" "INFO" "Cyan"
    } else {
        Write-RepairLog "ℹ️ 복구가 필요한 항목이 없습니다" "INFO" "Cyan"
    }
}

Write-RepairLog "로그 파일: $LogPath" "INFO" "Gray"
Write-RepairLog "완료 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO" "Gray"