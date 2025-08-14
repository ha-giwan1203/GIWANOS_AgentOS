param([switch]$VerboseMode)
$ErrorActionPreference = "Stop"

Import-Module (Join-Path (Get-Location) "tools\velos.common.psm1") -Force

$ROOT = Get-VelosRoot
$py = "python"
$summary = Join-Path $ROOT "data\reports\auto\self_check_summary.txt"
$logs = Join-Path $ROOT "data\logs"
$autofixLog = Join-Path $logs "autofix.log"
Ensure-Dirs -Paths @($logs, (Split-Path $summary -Parent))

$log = New-VelosLogger -Name "self_check" -LogPath $autofixLog
$env:PYTHONPATH = $ROOT

$probe = & $py (Join-Path $ROOT "modules\report_paths.py") 2>&1

$checks = @()
$checks += @{ name="VELOS_ROOT"; value=$ROOT; status="ok" }
$checks += @{ name="OPENAI_API_KEY"; value=($(if ($env:OPENAI_API_KEY) {"present"} else {"missing"})); status=($(if ($env:OPENAI_API_KEY) {"ok"} else {"warn"})) }
$checks += @{ name="Python"; value=$py; status="ok" }

$lines = @()
$lines += "=== VELOS Self Check Summary ==="
$lines += "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += "VELOS_ROOT: $ROOT"
$lines += ""
$lines += "[Probe Output]"
$lines += $probe
$lines += ""
$lines += "[Checks]"
foreach($c in $checks){ $lines += ("{0}: {1} ({2})" -f $c.name,$c.value,$c.status) }

$enc = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($summary, ($lines -join [Environment]::NewLine), $enc)
$log.Info("summary:$summary")

if($VerboseMode){ Get-Content $summary | Select-Object -First 40 | ForEach-Object { Write-Host $_ } }