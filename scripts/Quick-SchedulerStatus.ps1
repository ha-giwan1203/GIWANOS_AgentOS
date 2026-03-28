# [ACTIVE] VELOS 스케줄러 빠른 상태 확인 - 실시간 모니터링
# 적용된 최적화 시스템의 현재 작동 상태를 신속하게 점검

param(
    [switch]$Continuous,
    [int]$RefreshSeconds = 10,
    [switch]$ShowLogs,
    [switch]$Compact
)

function Get-VelosTaskStatus {
    try {
        $velosTasks = Get-ScheduledTask | Where-Object { 
            $_.TaskName -like "*VELOS*" -or 
            $_.TaskPath -like "*VELOS*" -or
            $_.Description -like "*VELOS*"
        }
        
        $status = @{
            TotalTasks = $velosTasks.Count
            ActiveTasks = ($velosTasks | Where-Object State -eq 'Ready').Count
            RunningTasks = ($velosTasks | Where-Object State -eq 'Running').Count
            HiddenTasks = ($velosTasks | Where-Object { $_.Settings.Hidden -eq $true }).Count
            LastRun = $null
            LastResult = $null
        }
        
        # 가장 최근 실행 정보
        $recentTask = $velosTasks | ForEach-Object {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $_.TaskName -ErrorAction SilentlyContinue
            if ($taskInfo -and $taskInfo.LastRunTime) {
                [PSCustomObject]@{
                    Name = $_.TaskName
                    LastRun = $taskInfo.LastRunTime
                    Result = $taskInfo.LastTaskResult
                }
            }
        } | Sort-Object LastRun -Descending | Select-Object -First 1
        
        if ($recentTask) {
            $status.LastRun = $recentTask.LastRun
            $status.LastResult = $recentTask.Result
        }
        
        return $status
    } catch {
        return @{Error = $_.Exception.Message}
    }
}

function Show-QuickStatus {
    param($Status, [switch]$IsCompact)
    
    Clear-Host
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    if (-not $IsCompact) {
        Write-Host "🔍 VELOS 스케줄러 실시간 상태 모니터링" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Gray
        Write-Host "업데이트: $timestamp" -ForegroundColor Gray
        Write-Host ""
    }
    
    if ($Status.Error) {
        Write-Host "❌ 오류: $($Status.Error)" -ForegroundColor Red
        return
    }
    
    # 기본 상태 정보
    $healthColor = if ($Status.ActiveTasks -gt 0) { "Green" } else { "Red" }
    $healthStatus = if ($Status.ActiveTasks -gt 0) { "정상" } else { "문제" }
    
    if ($IsCompact) {
        $compactInfo = "[$timestamp] 상태:$healthStatus | 총:$($Status.TotalTasks) | 활성:$($Status.ActiveTasks) | 실행중:$($Status.RunningTasks) | 숨김:$($Status.HiddenTasks)"
        Write-Host $compactInfo -ForegroundColor $healthColor
    } else {
        Write-Host "🎯 전체 상태: " -NoNewline
        Write-Host $healthStatus -ForegroundColor $healthColor
        Write-Host ""
        
        Write-Host "📊 태스크 통계:" -ForegroundColor Yellow
        Write-Host "  총 VELOS 태스크: $($Status.TotalTasks)개" -ForegroundColor White
        Write-Host "  활성 태스크: $($Status.ActiveTasks)개" -ForegroundColor Green
        Write-Host "  실행 중 태스크: $($Status.RunningTasks)개" -ForegroundColor Cyan
        Write-Host "  숨김 태스크: $($Status.HiddenTasks)개" -ForegroundColor Gray
        
        if ($Status.LastRun) {
            $timeDiff = (Get-Date) - $Status.LastRun
            $timeAgo = if ($timeDiff.TotalMinutes -lt 1) {
                "$([math]::Round($timeDiff.TotalSeconds))초 전"
            } elseif ($timeDiff.TotalHours -lt 1) {
                "$([math]::Round($timeDiff.TotalMinutes))분 전"
            } else {
                "$([math]::Round($timeDiff.TotalHours, 1))시간 전"
            }
            
            $resultColor = if ($Status.LastResult -eq 0) { "Green" } else { "Red" }
            $resultText = if ($Status.LastResult -eq 0) { "성공" } else { "오류(코드: $($Status.LastResult))" }
            
            Write-Host "`n⏰ 최근 실행:" -ForegroundColor Yellow
            Write-Host "  시간: $($Status.LastRun) ($timeAgo)" -ForegroundColor White
            Write-Host "  결과: " -NoNewline
            Write-Host $resultText -ForegroundColor $resultColor
        } else {
            Write-Host "`n⏰ 최근 실행 정보 없음" -ForegroundColor Yellow
        }
    }
    
    # 로그 표시
    if ($ShowLogs -and -not $IsCompact) {
        Write-Host "`n📋 최근 로그:" -ForegroundColor Yellow
        $logDir = "data\logs"
        if (Test-Path $logDir) {
            $recentLogs = Get-ChildItem $logDir -Filter "*.log" | 
                         Sort-Object LastWriteTime -Descending | 
                         Select-Object -First 3
            
            foreach ($log in $recentLogs) {
                $lastModified = $log.LastWriteTime.ToString("MM-dd HH:mm")
                Write-Host "  - $($log.Name) [$lastModified]" -ForegroundColor Gray
            }
        } else {
            Write-Host "  로그 디렉토리 없음" -ForegroundColor Red
        }
    }
    
    if ($Continuous -and -not $IsCompact) {
        Write-Host "`n🔄 자동 새로고침 중... (Ctrl+C로 중지)" -ForegroundColor Cyan
    }
}

# 메인 실행
if ($Continuous) {
    Write-Host "🔄 연속 모니터링 시작 (새로고침: ${RefreshSeconds}초 간격)" -ForegroundColor Green
    Write-Host "중지하려면 Ctrl+C를 누르세요..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
    
    while ($true) {
        try {
            $status = Get-VelosTaskStatus
            Show-QuickStatus -Status $status -IsCompact:$Compact
            Start-Sleep -Seconds $RefreshSeconds
        } catch {
            Write-Host "모니터링 오류: $($_.Exception.Message)" -ForegroundColor Red
            Start-Sleep -Seconds 5
        }
    }
} else {
    # 일회성 상태 확인
    $status = Get-VelosTaskStatus
    Show-QuickStatus -Status $status -IsCompact:$Compact
}

if (-not $Continuous) {
    Write-Host "`n💡 사용팁:" -ForegroundColor Cyan
    Write-Host "  연속 모니터링: .\scripts\Quick-SchedulerStatus.ps1 -Continuous" -ForegroundColor Gray
    Write-Host "  로그 포함: .\scripts\Quick-SchedulerStatus.ps1 -ShowLogs" -ForegroundColor Gray
    Write-Host "  압축 모드: .\scripts\Quick-SchedulerStatus.ps1 -Continuous -Compact" -ForegroundColor Gray
}