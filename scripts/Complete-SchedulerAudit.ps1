# [ACTIVE] VELOS 스케줄러 시스템 완전 재점검 및 성능 진단
# 적용 완료된 최적화 시스템의 실제 작동 상태를 종합 분석

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Detailed,
    [switch]$Performance,
    [switch]$RealTimeTest,
    [switch]$ExportReport,
    [string]$ReportPath = "data\reports\scheduler_audit_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
)

$ErrorActionPreference = 'Continue'
$Root = Get-Location
$StartTime = Get-Date

# 진단 결과 저장
$AuditResults = @{
    StartTime = $StartTime
    SystemInfo = @{}
    SchedulerStatus = @{}
    PerformanceMetrics = @{}
    Issues = @()
    Recommendations = @()
    Score = 0
}

function Write-AuditLog {
    param([string]$Message, [string]$Level = "INFO", [ConsoleColor]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $Color
    
    if ($ExportReport) {
        $logEntry | Out-File -FilePath $ReportPath -Append -Encoding UTF8
    }
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 헤더 출력
Clear-Host
Write-Host "🔍 VELOS 스케줄러 시스템 완전 재점검" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host "시작 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "실행 위치: $Root" -ForegroundColor Gray
Write-Host ""

# ═══════════════════════════════════════════════════════════════
# 1. 시스템 환경 점검
# ═══════════════════════════════════════════════════════════════
Write-AuditLog "🖥️ 1단계: 시스템 환경 기본 점검" "INFO" "Yellow"

# PowerShell 버전
$psVersion = $PSVersionTable.PSVersion
$AuditResults.SystemInfo.PowerShellVersion = "$($psVersion.Major).$($psVersion.Minor).$($psVersion.Patch)"
Write-AuditLog "  PowerShell 버전: $($AuditResults.SystemInfo.PowerShellVersion)" "INFO" "White"

if ($psVersion.Major -ge 7) {
    Write-AuditLog "  ✅ PowerShell 7.x - 병렬 처리 지원" "SUCCESS" "Green"
    $AuditResults.Score += 20
} elseif ($psVersion.Major -eq 5) {
    Write-AuditLog "  ⚠️ PowerShell 5.x - 병렬 처리 제한" "WARN" "Yellow"
    $AuditResults.Recommendations += "PowerShell 7 업그레이드 권장"
    $AuditResults.Score += 10
}

# 관리자 권한
$isAdmin = Test-AdminPrivileges
$AuditResults.SystemInfo.AdminPrivileges = $isAdmin
if ($isAdmin) {
    Write-AuditLog "  ✅ 관리자 권한으로 실행 중" "SUCCESS" "Green"
    $AuditResults.Score += 10
} else {
    Write-AuditLog "  ❌ 일반 사용자 권한 - 제한된 진단" "ERROR" "Red"
    $AuditResults.Issues += "관리자 권한 필요"
}

# 시스템 정보
try {
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $AuditResults.SystemInfo.OS = "$($osInfo.Caption) (Build $($osInfo.BuildNumber))"
    Write-AuditLog "  OS: $($AuditResults.SystemInfo.OS)" "INFO" "Gray"
} catch {
    Write-AuditLog "  ⚠️ OS 정보 수집 실패" "WARN" "Yellow"
}

# ═══════════════════════════════════════════════════════════════
# 2. VELOS 파일 시스템 점검
# ═══════════════════════════════════════════════════════════════
Write-AuditLog "`n📁 2단계: VELOS 파일 시스템 무결성 점검" "INFO" "Yellow"

$criticalFiles = @{
    "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml" = "최적화된 스케줄러 XML"
    "scripts\Invoke-VelosParallel.ps1" = "PowerShell 7.x 병렬 처리 스케줄러"
    "scripts\Start-Velos-CompletelyHidden.vbs" = "완전 숨김 VBS 런처"
    "scripts\Optimize-VelosScheduler.ps1" = "스케줄러 관리 도구"
    "scripts\velos_master_scheduler.py" = "마스터 스케줄러 Python 코드"
    "VELOS_SCHEDULER_OPTIMIZATION_GUIDE.md" = "사용법 가이드"
}

$missingFiles = @()
$corruptedFiles = @()

foreach ($file in $criticalFiles.Keys) {
    if (Test-Path $file) {
        $fileSize = (Get-Item $file).Length
        if ($fileSize -gt 0) {
            Write-AuditLog "  ✅ $file ($fileSize bytes)" "SUCCESS" "Green"
            $AuditResults.Score += 5
        } else {
            Write-AuditLog "  ❌ $file (빈 파일)" "ERROR" "Red"
            $corruptedFiles += $file
        }
    } else {
        Write-AuditLog "  ❌ $file (없음)" "ERROR" "Red"
        $missingFiles += $file
    }
}

$AuditResults.SystemInfo.MissingFiles = $missingFiles
$AuditResults.SystemInfo.CorruptedFiles = $corruptedFiles

if ($missingFiles.Count -eq 0 -and $corruptedFiles.Count -eq 0) {
    Write-AuditLog "  🎉 모든 필수 파일이 정상 상태입니다!" "SUCCESS" "Green"
    $AuditResults.Score += 10
} else {
    $AuditResults.Issues += "파일 시스템 문제: 누락 $($missingFiles.Count)개, 손상 $($corruptedFiles.Count)개"
}

# ═══════════════════════════════════════════════════════════════
# 3. Windows Task Scheduler 통합 상태
# ═══════════════════════════════════════════════════════════════
Write-AuditLog "`n📋 3단계: Windows Task Scheduler 통합 상태 점검" "INFO" "Yellow"

if ($isAdmin) {
    try {
        $allTasks = Get-ScheduledTask -ErrorAction Stop
        $velosTasks = $allTasks | Where-Object { 
            $_.TaskName -like "*VELOS*" -or 
            $_.TaskPath -like "*VELOS*" -or
            $_.Description -like "*VELOS*"
        }
        
        $AuditResults.SchedulerStatus.TotalVelosTasks = $velosTasks.Count
        
        if ($velosTasks.Count -eq 0) {
            Write-AuditLog "  ⚠️ 등록된 VELOS 스케줄드 태스크가 없습니다" "WARN" "Yellow"
            $AuditResults.Issues += "스케줄드 태스크 미등록"
        } else {
            Write-AuditLog "  📋 발견된 VELOS 태스크: $($velosTasks.Count)개" "INFO" "White"
            
            $activeTasks = 0
            $hiddenTasks = 0
            $optimizedTasks = 0
            
            foreach ($task in $velosTasks) {
                $taskInfo = Get-ScheduledTaskInfo -TaskName $task.TaskName -ErrorAction SilentlyContinue
                $isActive = $task.State -eq 'Ready'
                $isHidden = $task.Settings.Hidden -eq $true
                $isOptimized = $task.TaskName -like "*Hidden*" -or $task.TaskName -like "*Optimized*"
                
                if ($isActive) { $activeTasks++ }
                if ($isHidden) { $hiddenTasks++ }
                if ($isOptimized) { $optimizedTasks++ }
                
                $status = switch ($task.State) {
                    'Ready' { "✅ 활성" }
                    'Running' { "🔄 실행중" }
                    'Disabled' { "❌ 비활성" }
                    default { "❓ $($task.State)" }
                }
                
                $hiddenStatus = if ($isHidden) { "[숨김]" } else { "[표시]" }
                
                Write-AuditLog "    - $($task.TaskName) $status $hiddenStatus" "INFO" "Gray"
                
                if ($taskInfo) {
                    Write-AuditLog "      마지막 실행: $($taskInfo.LastRunTime)" "INFO" "DarkGray"
                    Write-AuditLog "      실행 결과: $($taskInfo.LastTaskResult)" "INFO" "DarkGray"
                }
            }
            
            $AuditResults.SchedulerStatus.ActiveTasks = $activeTasks
            $AuditResults.SchedulerStatus.HiddenTasks = $hiddenTasks
            $AuditResults.SchedulerStatus.OptimizedTasks = $optimizedTasks
            
            # 점수 계산
            if ($optimizedTasks -gt 0) {
                Write-AuditLog "  ✅ 최적화된 태스크 발견: $optimizedTasks개" "SUCCESS" "Green"
                $AuditResults.Score += 20
            }
            
            if ($hiddenTasks -gt 0) {
                Write-AuditLog "  ✅ 숨김 모드 태스크: $hiddenTasks개" "SUCCESS" "Green"
                $AuditResults.Score += 15
            }
            
            if ($activeTasks -gt 0) {
                Write-AuditLog "  ✅ 활성 태스크: $activeTasks개" "SUCCESS" "Green"
                $AuditResults.Score += 10
            }
            
            # 중복 태스크 검사
            $duplicates = $velosTasks | Group-Object TaskName | Where-Object Count -gt 1
            if ($duplicates.Count -gt 0) {
                Write-AuditLog "  ⚠️ 중복 태스크 발견: $($duplicates.Count)개" "WARN" "Yellow"
                $AuditResults.Issues += "중복 태스크 정리 필요"
                $AuditResults.Recommendations += ".\scripts\Optimize-VelosScheduler.ps1 -Cleanup 실행"
            }
        }
    } catch {
        Write-AuditLog "  ❌ Task Scheduler 접근 실패: $($_.Exception.Message)" "ERROR" "Red"
        $AuditResults.Issues += "Task Scheduler 접근 오류"
    }
} else {
    Write-AuditLog "  ⚠️ 관리자 권한 필요 - Task Scheduler 점검 제한" "WARN" "Yellow"
}

# ═══════════════════════════════════════════════════════════════
# 4. PowerShell 7.x 병렬 처리 성능 테스트
# ═══════════════════════════════════════════════════════════════
if ($Performance -and $psVersion.Major -ge 7) {
    Write-AuditLog "`n⚡ 4단계: PowerShell 7.x 병렬 처리 성능 테스트" "INFO" "Yellow"
    
    try {
        # 순차 처리 테스트
        $sequentialStart = Get-Date
        $sequentialResult = 1..10 | ForEach-Object { 
            Start-Sleep -Milliseconds 100
            return "Task $_"
        }
        $sequentialTime = (Get-Date) - $sequentialStart
        
        # 병렬 처리 테스트
        $parallelStart = Get-Date
        $parallelResult = 1..10 | ForEach-Object -Parallel { 
            Start-Sleep -Milliseconds 100
            return "Task $_"
        } -ThrottleLimit 5
        $parallelTime = (Get-Date) - $parallelStart
        
        $improvement = [math]::Round((($sequentialTime.TotalMilliseconds - $parallelTime.TotalMilliseconds) / $sequentialTime.TotalMilliseconds * 100), 2)
        
        Write-AuditLog "  순차 처리 시간: $([math]::Round($sequentialTime.TotalMilliseconds, 2))ms" "INFO" "Gray"
        Write-AuditLog "  병렬 처리 시간: $([math]::Round($parallelTime.TotalMilliseconds, 2))ms" "INFO" "Gray"
        Write-AuditLog "  성능 향상: $improvement%" "SUCCESS" "Green"
        
        $AuditResults.PerformanceMetrics.SequentialTime = $sequentialTime.TotalMilliseconds
        $AuditResults.PerformanceMetrics.ParallelTime = $parallelTime.TotalMilliseconds
        $AuditResults.PerformanceMetrics.Improvement = $improvement
        
        if ($improvement -gt 50) {
            Write-AuditLog "  🚀 병렬 처리 성능 우수!" "SUCCESS" "Green"
            $AuditResults.Score += 15
        } elseif ($improvement -gt 20) {
            Write-AuditLog "  ✅ 병렬 처리 성능 양호" "SUCCESS" "Green"
            $AuditResults.Score += 10
        } else {
            Write-AuditLog "  ⚠️ 병렬 처리 성능 제한적" "WARN" "Yellow"
            $AuditResults.Score += 5
        }
        
    } catch {
        Write-AuditLog "  ❌ 병렬 처리 테스트 실패: $($_.Exception.Message)" "ERROR" "Red"
        $AuditResults.Issues += "병렬 처리 기능 오류"
    }
}

# ═══════════════════════════════════════════════════════════════
# 5. 실시간 스케줄러 작동 테스트
# ═══════════════════════════════════════════════════════════════
if ($RealTimeTest -and $isAdmin) {
    Write-AuditLog "`n🔄 5단계: 실시간 스케줄러 작동 테스트" "INFO" "Yellow"
    
    try {
        # 최적화된 VELOS 태스크 찾기
        $targetTask = Get-ScheduledTask | Where-Object { 
            $_.TaskName -like "*VELOS*Hidden*" -or $_.TaskName -like "*VELOS*Optimized*"
        } | Select-Object -First 1
        
        if ($targetTask) {
            Write-AuditLog "  테스트 대상: $($targetTask.TaskName)" "INFO" "Gray"
            
            # 태스크 수동 실행
            $testStart = Get-Date
            Start-ScheduledTask -TaskName $targetTask.TaskName
            Write-AuditLog "  태스크 실행 시작..." "INFO" "Gray"
            
            # 5초 대기 후 상태 확인
            Start-Sleep -Seconds 5
            $taskInfo = Get-ScheduledTaskInfo -TaskName $targetTask.TaskName
            $testEnd = Get-Date
            
            Write-AuditLog "  마지막 실행 시간: $($taskInfo.LastRunTime)" "INFO" "Gray"
            Write-AuditLog "  실행 결과 코드: $($taskInfo.LastTaskResult)" "INFO" "Gray"
            
            if ($taskInfo.LastTaskResult -eq 0) {
                Write-AuditLog "  ✅ 스케줄러 정상 작동 확인!" "SUCCESS" "Green"
                $AuditResults.Score += 20
            } else {
                Write-AuditLog "  ⚠️ 스케줄러 실행 오류 (코드: $($taskInfo.LastTaskResult))" "WARN" "Yellow"
                $AuditResults.Issues += "스케줄러 실행 오류"
            }
        } else {
            Write-AuditLog "  ⚠️ 테스트할 최적화 태스크를 찾을 수 없음" "WARN" "Yellow"
            $AuditResults.Issues += "최적화된 태스크 없음"
        }
    } catch {
        Write-AuditLog "  ❌ 실시간 테스트 실패: $($_.Exception.Message)" "ERROR" "Red"
        $AuditResults.Issues += "실시간 테스트 오류"
    }
}

# ═══════════════════════════════════════════════════════════════
# 6. 로그 시스템 점검
# ═══════════════════════════════════════════════════════════════
Write-AuditLog "`n📊 6단계: 로그 시스템 및 모니터링 점검" "INFO" "Yellow"

$logDirectories = @("data\logs", "data\reports", "data\sessions")
$logFiles = @()

foreach ($logDir in $logDirectories) {
    if (Test-Path $logDir) {
        $files = Get-ChildItem $logDir -Recurse -File | Sort-Object LastWriteTime -Descending
        $logFiles += $files
        Write-AuditLog "  ✅ $logDir : $($files.Count)개 파일" "SUCCESS" "Green"
        $AuditResults.Score += 5
        
        # 최근 로그 파일 확인
        $recentFiles = $files | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-1) }
        if ($recentFiles.Count -gt 0) {
            Write-AuditLog "    최근 24시간 로그: $($recentFiles.Count)개" "INFO" "Gray"
        }
    } else {
        Write-AuditLog "  ❌ $logDir : 디렉토리 없음" "ERROR" "Red"
        $AuditResults.Issues += "$logDir 디렉토리 미생성"
    }
}

# 총 로그 파일 크기
if ($logFiles.Count -gt 0) {
    $totalSize = ($logFiles | Measure-Object -Property Length -Sum).Sum
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-AuditLog "  📊 총 로그 크기: ${totalSizeMB}MB ($($logFiles.Count)개 파일)" "INFO" "Gray"
    
    $AuditResults.SystemInfo.LogFileCount = $logFiles.Count
    $AuditResults.SystemInfo.LogSizeMB = $totalSizeMB
}

# ═══════════════════════════════════════════════════════════════
# 7. 최종 점수 계산 및 등급 평가
# ═══════════════════════════════════════════════════════════════
$endTime = Get-Date
$duration = $endTime - $StartTime
$AuditResults.EndTime = $endTime
$AuditResults.Duration = $duration

# 등급 계산
$grade = switch ($AuditResults.Score) {
    {$_ -ge 90} { @{Grade="A+"; Color="Green"; Description="최적 상태"} }
    {$_ -ge 80} { @{Grade="A"; Color="Green"; Description="우수"} }
    {$_ -ge 70} { @{Grade="B+"; Color="Cyan"; Description="양호"} }
    {$_ -ge 60} { @{Grade="B"; Color="Yellow"; Description="보통"} }
    {$_ -ge 50} { @{Grade="C"; Color="Yellow"; Description="개선 필요"} }
    default { @{Grade="F"; Color="Red"; Description="심각한 문제"} }
}

# 최종 결과 출력
Write-Host "`n" + "=" * 80 -ForegroundColor Gray
Write-Host "🎯 VELOS 스케줄러 시스템 진단 완료" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray

Write-Host "`n📊 최종 평가 결과:" -ForegroundColor White
Write-Host "  등급: $($grade.Grade) - $($grade.Description)" -ForegroundColor $grade.Color
Write-Host "  점수: $($AuditResults.Score)/100" -ForegroundColor $grade.Color
Write-Host "  소요시간: $([math]::Round($duration.TotalSeconds, 1))초" -ForegroundColor Gray

if ($AuditResults.Issues.Count -gt 0) {
    Write-Host "`n❌ 발견된 문제점 ($($AuditResults.Issues.Count)개):" -ForegroundColor Red
    foreach ($issue in $AuditResults.Issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
}

if ($AuditResults.Recommendations.Count -gt 0) {
    Write-Host "`n💡 권장사항 ($($AuditResults.Recommendations.Count)개):" -ForegroundColor Yellow
    foreach ($rec in $AuditResults.Recommendations) {
        Write-Host "  - $rec" -ForegroundColor Yellow
    }
}

# 다음 단계 안내
Write-Host "`n🚀 다음 단계:" -ForegroundColor Cyan
if ($AuditResults.Score -ge 80) {
    Write-Host "  ✅ 시스템이 최적 상태입니다!" -ForegroundColor Green
    Write-Host "  📋 정기 모니터링 권장: 주간 1회 재점검" -ForegroundColor Gray
} elseif ($AuditResults.Score -ge 60) {
    Write-Host "  ⚠️ 일부 개선이 필요합니다" -ForegroundColor Yellow
    Write-Host "  📋 권장사항 적용 후 재점검 실행" -ForegroundColor Gray
} else {
    Write-Host "  ❌ 시급한 문제 해결 필요" -ForegroundColor Red
    Write-Host "  📋 기본 설치부터 다시 시작 권장" -ForegroundColor Gray
    Write-Host "  🔧 명령어: .\scripts\Optimize-VelosScheduler.ps1 -Install -Force" -ForegroundColor White
}

# 보고서 내보내기
if ($ExportReport) {
    Write-Host "`n📄 상세 보고서 저장됨: $ReportPath" -ForegroundColor Cyan
}

Write-Host "`n완료 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray