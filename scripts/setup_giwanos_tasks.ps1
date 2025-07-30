
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries:$true `
    -DontStopIfGoingOnBatteries:$true

$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\giwanos\run_giwanos_master_loop.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName "GIWANOS_Master_Loop" -Description "Runs the GIWANOS Master Loop daily at 8am" -User "SYSTEM"

$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\giwanos\automation\disk_cleanup.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName "GIWANOS_Disk_Cleanup" -Description "Runs the GIWANOS Disk Cleanup daily at 9am" -User "SYSTEM"

$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\giwanos\evaluation\evaluation_feedback_loop.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 10am
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName "GIWANOS_Evaluation_Feedback" -Description "Runs GIWANOS Evaluation Feedback Loop daily at 10am" -User "SYSTEM"

$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\giwanos\automation\process_management.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 11am
Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName "GIWANOS_Process_Management" -Description "Runs GIWANOS Process Management daily at 11am" -User "SYSTEM"
