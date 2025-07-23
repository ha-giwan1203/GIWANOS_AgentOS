
$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\giwanos\run_giwanos_full_loop.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "GIWANOS_FullLoop_Daily" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
