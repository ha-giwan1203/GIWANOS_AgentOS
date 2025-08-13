$DefaultRoot = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")) }
# start_velos_bridge.ps1 - robust starter for Task Scheduler
$ErrorActionPreference = "Stop"

$py   = "$(if ($env:VELOS_PYTHON) { $env:VELOS_PYTHON } else { "python" })"

# 브리지 전용 우회 플래그
$env:VELOS_ALLOW_BRIDGE = "1"
$env:VELOS_DB_WRITE_FORBIDDEN = "1"
$env:PYTHONPATH = $root

Set-Location $root
& $py "$root\scripts\velos_bridge.py"










