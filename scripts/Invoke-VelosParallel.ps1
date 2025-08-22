#Requires -Version 7.0
# [ACTIVE] VELOS PowerShell 7 병렬 처리 최적화 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

param(
    [string[]]$Tasks = @("memory_tick", "health_check", "report_generation"),
    [int]$ThrottleLimit = 3,
    [switch]$Verbose = $false
)

$ErrorActionPreference = 'Stop'
$Root = 'C:\giwanos'

Write-Host "=== VELOS PowerShell 7 병렬 실행 ===" -ForegroundColor Cyan
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor Green
Write-Host "병렬 작업 수: $($Tasks.Count)" -ForegroundColor Yellow
Write-Host "동시 실행 제한: $ThrottleLimit" -ForegroundColor Yellow

# PowerShell 7의 ForEach-Object -Parallel 활용
$results = $Tasks | ForEach-Object -Parallel {
    $task = $_
    $root = $using:Root
    $verbose = $using:Verbose
    
    $startTime = Get-Date
    
    try {
        switch ($task) {
            "memory_tick" {
                $result = & python "$root\scripts\memory_tick.py"
            }
            "health_check" {
                $result = & python "$root\scripts\check_integrity.py"
            }
            "report_generation" {
                $result = & python "$root\scripts\generate_velos_report.py"
            }
            default {
                throw "Unknown task: $task"
            }
        }
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalMilliseconds
        
        [PSCustomObject]@{
            Task = $task
            Status = "Success"
            Duration = $duration
            Result = $result
            StartTime = $startTime
            EndTime = $endTime
        }
    }
    catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalMilliseconds
        
        [PSCustomObject]@{
            Task = $task
            Status = "Failed"
            Duration = $duration
            Error = $_.Exception.Message
            StartTime = $startTime
            EndTime = $endTime
        }
    }
} -ThrottleLimit $ThrottleLimit

# 결과 출력
Write-Host "`n=== 실행 결과 ===" -ForegroundColor Cyan
$results | ForEach-Object {
    $statusColor = if ($_.Status -eq "Success") { "Green" } else { "Red" }
    Write-Host "[$($_.Task)] $($_.Status) - $([math]::Round($_.Duration, 2))ms" -ForegroundColor $statusColor
    
    if ($Verbose -and $_.Result) {
        Write-Host "  출력: $($_.Result)" -ForegroundColor Gray
    }
    
    if ($_.Error) {
        Write-Host "  오류: $($_.Error)" -ForegroundColor Red
    }
}

# 통계
$successCount = ($results | Where-Object { $_.Status -eq "Success" }).Count
$totalDuration = ($results | Measure-Object Duration -Sum).Sum

Write-Host "`n=== 통계 ===" -ForegroundColor Cyan
Write-Host "성공: $successCount/$($Tasks.Count)" -ForegroundColor Green
Write-Host "총 소요시간: $([math]::Round($totalDuration, 2))ms" -ForegroundColor Yellow

# JSON 형태로 결과 저장 (PowerShell 7의 향상된 JSON 지원)
$logPath = Join-Path $Root "data\logs\parallel_execution_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$results | ConvertTo-Json -Depth 3 -Compress:$false | Out-File -FilePath $logPath -Encoding UTF8

Write-Host "결과 로그 저장: $logPath" -ForegroundColor Gray