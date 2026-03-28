# [ACTIVE] VELOS PowerShell 7.x 병렬 처리 스케줄러 - ForEach-Object -Parallel 최적화
# =========================================================
# VELOS 운영 철학: 병렬 처리를 통한 성능 최적화
# PowerShell 7.x의 ForEach-Object -Parallel 기능 활용
# =========================================================

#Requires -Version 7.0

[CmdletBinding()]
param(
    [string]$ConfigPath = "C:\giwanos\data\parallel_jobs.json",
    [switch]$DryRun,
    [int]$ThrottleLimit = 5,
    [switch]$Verbose
)

$ErrorActionPreference = 'Continue'
$Root = 'C:\giwanos'

# 로그 설정
$LogPath = Join-Path $Root "data\logs\parallel_scheduler_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
New-Item -ItemType Directory -Path (Split-Path $LogPath) -Force -ErrorAction SilentlyContinue | Out-Null

function Write-VelosLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

# 병렬 작업 설정 기본값 생성
if (-not (Test-Path $ConfigPath)) {
    $defaultConfig = @{
        jobs = @(
            @{
                name = "health_check"
                script = "scripts\health_monitor.py"
                interval_minutes = 5
                parallel_safe = $true
                timeout_seconds = 120
            },
            @{
                name = "memory_tick"
                script = "scripts\memory_tick.py" 
                interval_minutes = 10
                parallel_safe = $true
                timeout_seconds = 300
            },
            @{
                name = "report_dispatch"
                script = "scripts\dispatch_report.py"
                interval_minutes = 15
                parallel_safe = $false
                timeout_seconds = 600
            },
            @{
                name = "log_cleanup"
                script = "scripts\log_rotate.ps1"
                interval_minutes = 60
                parallel_safe = $true
                timeout_seconds = 180
                type = "powershell"
            }
        )
        settings = @{
            max_parallel = 5
            default_timeout = 300
            log_retention_days = 7
        }
    }
    
    $defaultConfig | ConvertTo-Json -Depth 4 | Out-File -FilePath $ConfigPath -Encoding UTF8
    Write-VelosLog "기본 병렬 작업 설정 파일 생성: $ConfigPath"
}

# 설정 로드
try {
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    Write-VelosLog "병렬 작업 설정 로드 완료: $($config.jobs.Count)개 작업"
}
catch {
    Write-VelosLog "설정 파일 로드 실패: $_" "ERROR"
    exit 1
}

# 상태 파일 경로
$stateFile = Join-Path $Root "data\parallel_job_state.json"
$lastRun = @{}

if (Test-Path $stateFile) {
    try {
        $lastRun = Get-Content $stateFile | ConvertFrom-Json -AsHashtable
    }
    catch {
        Write-VelosLog "상태 파일 로드 실패, 새로 시작: $_" "WARN"
    }
}

# 실행할 작업 필터링
$currentTime = Get-Date
$jobsToRun = $config.jobs | Where-Object {
    $jobName = $_.name
    $intervalMinutes = $_.interval_minutes
    
    if (-not $lastRun[$jobName]) {
        return $true
    }
    
    $lastRunTime = [DateTime]::Parse($lastRun[$jobName])
    $elapsedMinutes = ($currentTime - $lastRunTime).TotalMinutes
    
    return $elapsedMinutes -ge $intervalMinutes
}

Write-VelosLog "실행 대상 작업: $($jobsToRun.Count)개"

if ($jobsToRun.Count -eq 0) {
    Write-VelosLog "실행할 작업이 없습니다."
    exit 0
}

if ($DryRun) {
    Write-VelosLog "DRY RUN 모드 - 실제 실행하지 않음"
    $jobsToRun | ForEach-Object {
        Write-VelosLog "  - $($_.name): $($_.script)"
    }
    exit 0
}

# 병렬 실행과 순차 실행 분리
$parallelJobs = $jobsToRun | Where-Object { $_.parallel_safe -eq $true }
$sequentialJobs = $jobsToRun | Where-Object { $_.parallel_safe -ne $true }

Write-VelosLog "병렬 실행 작업: $($parallelJobs.Count)개"
Write-VelosLog "순차 실행 작업: $($sequentialJobs.Count)개"

# PowerShell 7.x 병렬 실행
if ($parallelJobs.Count -gt 0) {
    Write-VelosLog "PowerShell 7.x 병렬 처리 시작..."
    
    $parallelResults = $parallelJobs | ForEach-Object -Parallel {
        $job = $_
        $Root = $using:Root
        $currentTime = $using:currentTime
        
        # 로그 함수를 병렬 블록 내에서 재정의
        function Write-ParallelLog {
            param([string]$Message, [string]$Level = "INFO", [string]$JobName = "")
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $logEntry = "[$timestamp] [$Level] [$JobName] $Message"
            return $logEntry
        }
        
        try {
            $timeout = if ($job.timeout_seconds) { $job.timeout_seconds } else { 300 }
            $scriptPath = Join-Path $Root $job.script
            
            if (-not (Test-Path $scriptPath)) {
                return Write-ParallelLog "스크립트 파일이 없습니다: $scriptPath" "ERROR" $job.name
            }
            
            $startTime = Get-Date
            
            # 스크립트 유형에 따른 실행
            if ($job.type -eq "powershell") {
                $process = Start-Process -FilePath "pwsh.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`"" -WindowStyle Hidden -PassThru -WorkingDirectory $Root
            } else {
                # Python 스크립트 (기본)
                $venvPath = if (Test-Path (Join-Path $Root ".venv_link")) { 
                    Get-Content (Join-Path $Root ".venv_link") 
                } else { 
                    Join-Path $Root ".venv" 
                }
                $python = Join-Path $venvPath "Scripts\python.exe"
                if (-not (Test-Path $python)) { $python = "python" }
                
                $env:PYTHONPATH = $Root
                $env:VELOS_ROOT = $Root
                $process = Start-Process -FilePath $python -ArgumentList "`"$scriptPath`"" -WindowStyle Hidden -PassThru -WorkingDirectory $Root
            }
            
            if (-not $process.WaitForExit($timeout * 1000)) {
                $process.Kill()
                return Write-ParallelLog "타임아웃으로 인한 강제 종료 (${timeout}초)" "WARN" $job.name
            }
            
            $duration = (Get-Date) - $startTime
            return Write-ParallelLog "실행 완료 (소요시간: $([math]::Round($duration.TotalSeconds, 2))초, 종료코드: $($process.ExitCode))" "INFO" $job.name
            
        }
        catch {
            return Write-ParallelLog "실행 중 오류: $($_.Exception.Message)" "ERROR" $job.name
        }
    } -ThrottleLimit $ThrottleLimit
    
    # 병렬 실행 결과 로그 출력
    $parallelResults | ForEach-Object {
        Write-Host $_
        $_ | Out-File -FilePath $LogPath -Append -Encoding UTF8
    }
}

# 순차 실행 작업
if ($sequentialJobs.Count -gt 0) {
    Write-VelosLog "순차 실행 작업 처리 시작..."
    
    foreach ($job in $sequentialJobs) {
        try {
            $timeout = if ($job.timeout_seconds) { $job.timeout_seconds } else { 300 }
            $scriptPath = Join-Path $Root $job.script
            
            if (-not (Test-Path $scriptPath)) {
                Write-VelosLog "스크립트 파일이 없습니다: $scriptPath" "ERROR"
                continue
            }
            
            Write-VelosLog "순차 실행 시작: $($job.name)"
            $startTime = Get-Date
            
            # 스크립트 유형에 따른 실행
            if ($job.type -eq "powershell") {
                $process = Start-Process -FilePath "pwsh.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`"" -WindowStyle Hidden -PassThru -WorkingDirectory $Root
            } else {
                # Python 스크립트 (기본)
                $venvPath = if (Test-Path (Join-Path $Root ".venv_link")) { 
                    Get-Content (Join-Path $Root ".venv_link") 
                } else { 
                    Join-Path $Root ".venv" 
                }
                $python = Join-Path $venvPath "Scripts\python.exe"
                if (-not (Test-Path $python)) { $python = "python" }
                
                $env:PYTHONPATH = $Root
                $env:VELOS_ROOT = $Root
                $process = Start-Process -FilePath $python -ArgumentList "`"$scriptPath`"" -WindowStyle Hidden -PassThru -WorkingDirectory $Root
            }
            
            if (-not $process.WaitForExit($timeout * 1000)) {
                $process.Kill()
                Write-VelosLog "타임아웃으로 인한 강제 종료: $($job.name) (${timeout}초)" "WARN"
                continue
            }
            
            $duration = (Get-Date) - $startTime
            Write-VelosLog "순차 실행 완료: $($job.name) (소요시간: $([math]::Round($duration.TotalSeconds, 2))초, 종료코드: $($process.ExitCode))"
            
        }
        catch {
            Write-VelosLog "순차 실행 중 오류: $($job.name) - $($_.Exception.Message)" "ERROR"
        }
    }
}

# 상태 업데이트
$jobsToRun | ForEach-Object {
    $lastRun[$_.name] = $currentTime.ToString("yyyy-MM-ddTHH:mm:ss")
}

try {
    $lastRun | ConvertTo-Json -Depth 2 | Out-File -FilePath $stateFile -Encoding UTF8
    Write-VelosLog "작업 상태 업데이트 완료"
}
catch {
    Write-VelosLog "상태 파일 저장 실패: $_" "ERROR"
}

Write-VelosLog "VELOS 병렬 스케줄러 실행 완료"