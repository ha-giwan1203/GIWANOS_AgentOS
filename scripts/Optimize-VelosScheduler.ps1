# [ACTIVE] VELOS 스케줄러 최적화 및 통합 관리 스크립트
# PowerShell 7.x + 완전 숨김 모드 + 중복 제거

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Remove,
    [switch]$Status,
    [switch]$Cleanup,
    [switch]$Force,
    [switch]$WhatIf
)

# 관리자 권한 확인
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "❌ 관리자 권한이 필요합니다. PowerShell을 관리자 권한으로 실행해주세요." -ForegroundColor Red
    exit 1
}

$Root = "C:\giwanos"
$LogPath = Join-Path $Root "data\logs\scheduler_optimizer.log"

function Write-OptLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    New-Item -ItemType Directory -Path (Split-Path $LogPath) -Force -ErrorAction SilentlyContinue | Out-Null
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

# 기존 VELOS 관련 태스크 찾기
function Get-VelosScheduledTasks {
    return Get-ScheduledTask | Where-Object { 
        $_.TaskName -like "*VELOS*" -or 
        $_.TaskPath -like "*VELOS*" -or
        $_.Description -like "*VELOS*"
    }
}

# 상태 확인
if ($Status) {
    Write-OptLog "VELOS 스케줄러 상태 확인 중..."
    
    $velosTasks = Get-VelosScheduledTasks
    
    if ($velosTasks.Count -eq 0) {
        Write-Host "🔍 등록된 VELOS 스케줄드 태스크가 없습니다." -ForegroundColor Yellow
    } else {
        Write-Host "📋 발견된 VELOS 스케줄드 태스크:" -ForegroundColor Cyan
        foreach ($task in $velosTasks) {
            $status = if ($task.State -eq 'Ready') { "✅ 활성" } else { "❌ 비활성" }
            Write-Host "  - $($task.TaskName) [$status]" -ForegroundColor White
            Write-Host "    경로: $($task.TaskPath)" -ForegroundColor Gray
            if ($task.Description) {
                Write-Host "    설명: $($task.Description)" -ForegroundColor Gray
            }
        }
    }
    
    # PowerShell 버전 확인
    $psVersion = $PSVersionTable.PSVersion
    Write-Host "🔧 PowerShell 버전: $($psVersion.Major).$($psVersion.Minor)" -ForegroundColor Cyan
    
    if ($psVersion.Major -ge 7) {
        Write-Host "✅ PowerShell 7.x 감지 - 병렬 처리 기능 사용 가능" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PowerShell $($psVersion.Major).$($psVersion.Minor) - 병렬 처리 제한됨" -ForegroundColor Yellow
    }
    
    exit 0
}

# 중복 태스크 정리
if ($Cleanup) {
    Write-OptLog "중복 VELOS 태스크 정리 시작..."
    
    $velosTasks = Get-VelosScheduledTasks
    $tasksToKeep = @()
    $tasksToRemove = @()
    
    # 우선순위: Hidden > Optimized > Fixed > Improved > 기타
    $priorityOrder = @("Hidden", "Optimized", "Fixed", "Improved")
    
    foreach ($priority in $priorityOrder) {
        $matchingTasks = $velosTasks | Where-Object { $_.TaskName -like "*$priority*" }
        if ($matchingTasks.Count -gt 0) {
            $tasksToKeep += $matchingTasks[0]  # 첫 번째만 유지
            if ($matchingTasks.Count -gt 1) {
                $tasksToRemove += $matchingTasks[1..($matchingTasks.Count-1)]
            }
        }
    }
    
    # 우선순위에 없는 태스크들은 모두 제거 대상
    $otherTasks = $velosTasks | Where-Object { 
        $taskName = $_.TaskName
        -not ($priorityOrder | Where-Object { $taskName -like "*$_*" })
    }
    $tasksToRemove += $otherTasks
    
    if ($tasksToRemove.Count -gt 0) {
        Write-Host "🗑️  제거할 중복 태스크:" -ForegroundColor Yellow
        foreach ($task in $tasksToRemove) {
            Write-Host "  - $($task.TaskName)" -ForegroundColor Red
            if (-not $WhatIf) {
                try {
                    Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                    Write-OptLog "중복 태스크 제거 완료: $($task.TaskName)"
                }
                catch {
                    Write-OptLog "태스크 제거 실패: $($task.TaskName) - $_" "ERROR"
                }
            }
        }
    } else {
        Write-Host "✅ 중복 태스크가 없습니다." -ForegroundColor Green
    }
    
    if ($WhatIf) {
        Write-Host "🔍 WhatIf 모드 - 실제 제거하지 않음" -ForegroundColor Cyan
    }
    
    exit 0
}

# 기존 태스크 모두 제거
if ($Remove) {
    Write-OptLog "모든 VELOS 태스크 제거 시작..."
    
    $velosTasks = Get-VelosScheduledTasks
    
    if ($velosTasks.Count -eq 0) {
        Write-Host "ℹ️  제거할 VELOS 태스크가 없습니다." -ForegroundColor Yellow
        exit 0
    }
    
    foreach ($task in $velosTasks) {
        Write-Host "🗑️  제거 중: $($task.TaskName)" -ForegroundColor Yellow
        if (-not $WhatIf) {
            try {
                Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                Write-OptLog "태스크 제거 완료: $($task.TaskName)"
            }
            catch {
                Write-OptLog "태스크 제거 실패: $($task.TaskName) - $_" "ERROR"
            }
        }
    }
    
    Write-Host "✅ VELOS 태스크 제거 완료" -ForegroundColor Green
    exit 0
}

# 최적화된 스케줄러 설치
if ($Install) {
    Write-OptLog "VELOS 최적화 스케줄러 설치 시작..."
    
    # 기존 태스크 정리 (Force 옵션 시)
    if ($Force) {
        Write-Host "🧹 기존 VELOS 태스크 정리 중..." -ForegroundColor Yellow
        $velosTasks = Get-VelosScheduledTasks
        foreach ($task in $velosTasks) {
            try {
                Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                Write-OptLog "기존 태스크 제거: $($task.TaskName)"
            }
            catch {
                Write-OptLog "기존 태스크 제거 실패: $($task.TaskName) - $_" "WARN"
            }
        }
    }
    
    # XML 경로
    $xmlPath = Join-Path $Root "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml"
    
    if (-not (Test-Path $xmlPath)) {
        Write-Host "❌ 최적화된 XML 파일이 없습니다: $xmlPath" -ForegroundColor Red
        Write-OptLog "XML 파일 없음: $xmlPath" "ERROR"
        exit 1
    }
    
    # 태스크 등록
    $taskName = "VELOS Master Scheduler Hidden"
    
    if (-not $WhatIf) {
        try {
            Register-ScheduledTask -Xml (Get-Content $xmlPath | Out-String) -TaskName $taskName -Force
            Write-Host "✅ 최적화된 VELOS 스케줄러 등록 완료: $taskName" -ForegroundColor Green
            Write-OptLog "스케줄러 등록 완료: $taskName"
            
            # 태스크 활성화 확인
            $newTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($newTask -and $newTask.State -eq 'Ready') {
                Write-Host "✅ 태스크가 활성 상태입니다." -ForegroundColor Green
                
                # 즉시 테스트 실행
                if ($Force) {
                    Write-Host "🚀 테스트 실행 중..." -ForegroundColor Cyan
                    Start-ScheduledTask -TaskName $taskName
                    Start-Sleep -Seconds 3
                    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
                    Write-Host "📊 마지막 실행: $($taskInfo.LastRunTime)" -ForegroundColor Cyan
                    Write-Host "📊 마지막 결과: $($taskInfo.LastTaskResult)" -ForegroundColor Cyan
                }
            } else {
                Write-Host "⚠️  태스크가 비활성 상태입니다." -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "❌ 스케줄러 등록 실패: $_" -ForegroundColor Red
            Write-OptLog "스케줄러 등록 실패: $_" "ERROR"
            exit 1
        }
    } else {
        Write-Host "🔍 WhatIf 모드 - 실제 등록하지 않음" -ForegroundColor Cyan
        Write-Host "등록할 태스크: $taskName" -ForegroundColor White
        Write-Host "XML 파일: $xmlPath" -ForegroundColor White
    }
    
    exit 0
}

# 기본 동작: 상태 표시
Write-Host "🔧 VELOS 스케줄러 최적화 도구" -ForegroundColor Cyan
Write-Host ""
Write-Host "사용법:" -ForegroundColor White
Write-Host "  -Status    현재 상태 확인" -ForegroundColor Gray
Write-Host "  -Install   최적화된 스케줄러 설치" -ForegroundColor Gray
Write-Host "  -Remove    모든 VELOS 태스크 제거" -ForegroundColor Gray
Write-Host "  -Cleanup   중복 태스크만 정리" -ForegroundColor Gray
Write-Host "  -Force     강제 실행 (기존 태스크 덮어쓰기)" -ForegroundColor Gray
Write-Host "  -WhatIf    실제 변경 없이 미리보기" -ForegroundColor Gray
Write-Host ""
Write-Host "예시:" -ForegroundColor White
Write-Host "  .\Optimize-VelosScheduler.ps1 -Status" -ForegroundColor Yellow
Write-Host "  .\Optimize-VelosScheduler.ps1 -Install -Force" -ForegroundColor Yellow
Write-Host "  .\Optimize-VelosScheduler.ps1 -Cleanup -WhatIf" -ForegroundColor Yellow