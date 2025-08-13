# PowerShell runner: Master → Bridge(once)
$ErrorActionPreference = "Stop"
$root = "C:\giwanos"
Set-Location $root

# Python 우선 실행자
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $pycmd = "py -3" } else { $pycmd = "python" }

# 1) 마스터
& $pycmd scripts\run_giwanos_master_loop.py

# 2) 브릿지(1회 처리)
& $pycmd scripts\velos_bridge.py --once
