param([switch]$DryRun)
$env:PYTHONPATH = 'C:\giwanos'
& 'C:\Users\User\venvs\velos\Scripts\Activate.ps1'
if ($DryRun) { python 'C:\giwanos\scripts\run_giwanos_master_loop.py' --dry-run }
else { python 'C:\giwanos\scripts\run_giwanos_master_loop.py' }


