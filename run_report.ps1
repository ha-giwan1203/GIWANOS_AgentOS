$ErrorActionPreference = "Stop"
$root = "C:\giwanos"
Set-Location $root
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $pycmd = "py -3" } else { $pycmd = "python" }
& $pycmd scripts\run_giwanos_master_loop.py
