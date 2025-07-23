$taskName = "GIWANOS_Daily_Run"

# 스케줄러 등록 여부 확인
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($null -eq $task) {
    Write-Output "❌ GIWANOS 스케줄러가 등록되어 있지 않습니다."
} else {
    Write-Output "✅ 스케줄러 등록 확인됨: $taskName"
    Write-Output "▶ 다음 실행 시간: " $task.Triggers.StartBoundary
    Write-Output "▶ 실행 경로: " $task.Actions.Execute $task.Actions.Arguments
}

# 최근 실행 로그 파일 경로
$logPath = "C:\giwanos\agent_logs"
if (Test-Path $logPath) {
    $recent = Get-ChildItem $logPath\agent_log_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($recent) {
        Write-Output "📝 최근 실행 로그: $($recent.Name)"
        Write-Output "📅 시간: $($recent.LastWriteTime)"
    } else {
        Write-Output "⚠️ 실행 로그 파일이 없습니다."
    }
} else {
    Write-Output "⚠️ agent_logs 폴더가 존재하지 않습니다."
}
