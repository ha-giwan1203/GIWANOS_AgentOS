# register_watch_task.ps1
# watch_changes.py 작업 스케줄러 등록
# PowerShell 5+ 필요

$taskName = "업무리스트_파일감시"
$vbsPath  = "C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\watch_changes_launcher.vbs"
$workDir  = "C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리"

Write-Host "[1/4] 기존 작업 제거..."
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "[2/4] 트리거 / 액션 / 설정 구성..."

# 트리거: 로그온 시 (현재 사용자), 30초 지연
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$trigger.Delay = "PT30S"

# 액션: wscript.exe 로 VBS 실행 (창 없음)
$action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "`"$vbsPath`"" `
    -WorkingDirectory $workDir

# 설정
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -DontStopOnIdleEnd

# 실패 재시작: 1분 간격 3회
$settings.RestartInterval = "PT1M"
$settings.RestartCount    = 3

Write-Host "[3/4] 작업 등록..."
Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger  $trigger `
    -Action   $action `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "[4/4] 등록 결과:"
$task = Get-ScheduledTask -TaskName $taskName
[PSCustomObject]@{
    TaskName  = $task.TaskName
    State     = $task.State
    Trigger   = ($task.Triggers | ForEach-Object { $_.CimClass.CimClassName }) -join ", "
    Action    = $task.Actions[0].Execute + " " + $task.Actions[0].Arguments
    WorkDir   = $task.Actions[0].WorkingDirectory
    RunLevel  = $task.Principal.RunLevel
    RestartInterval = $task.Settings.RestartInterval
    RestartCount    = $task.Settings.RestartCount
} | Format-List

Write-Host ""
Write-Host "수동 실행 테스트 명령:"
Write-Host "  schtasks /run /tn `"$taskName`""
