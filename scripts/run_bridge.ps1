# run_bridge.ps1 — venv 강제 + 브릿지만 실행
$ErrorActionPreference = 'Stop'
. (Join-Path (Join-Path  'scripts') '_venv_bootstrap.ps1') -VenvPath  -EnvFilePath (Join-Path  '.env')
python (Join-Path (Join-Path  'scripts') 'velos_bridge.py')

