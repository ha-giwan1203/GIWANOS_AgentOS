# 기존 작업 삭제
$taskName = "GIWANOS_Master_Loop"
Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# 작업 액션 정의 (PYTHONPATH 환경변수 포함)
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c "set PYTHONPATH=C:\giwanos && python C:\giwanos\system\run_giwanos_master_loop.py"'

# 매일 오전 8시에 트리거 정의
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# 최고 권한으로 작업 등록
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# 작업 등록
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal

Write-Host "GIWANOS 작업 스케줄러가 성공적으로 재설정되었습니다."