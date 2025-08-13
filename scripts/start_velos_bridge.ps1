# start_velos_bridge.ps1 - robust starter for Task Scheduler
$ErrorActionPreference = "Stop"

$root = "C:\giwanos"
$py   = "C:\Users\User\venvs\velos\Scripts\python.exe"

# 브리지 전용 우회 플래그
$env:VELOS_ALLOW_BRIDGE = "1"
$env:VELOS_DB_WRITE_FORBIDDEN = "1"
$env:PYTHONPATH = $root

Set-Location $root
& $py "$root\scripts\velos_bridge.py"


