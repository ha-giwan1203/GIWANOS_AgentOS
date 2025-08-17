@echo off
echo Creating VELOS-MasterLoop scheduled task...
schtasks /create /tn "VELOS-MasterLoop" /sc minute /mo 10 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\giwanos\scripts\velos_master_loop_wrapper.ps1" /f
if %errorlevel% equ 0 (
    echo Task created successfully!
    schtasks /query /tn "VELOS-MasterLoop" /fo list
) else (
    echo Failed to create task. Error code: %errorlevel%
)
pause
