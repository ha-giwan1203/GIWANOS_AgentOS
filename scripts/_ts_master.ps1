$ErrorActionPreference="Stop"
$root="C:\giwanos"
$log = Join-Path $root ("data\logs\ts_master_" + (Get-Date -Format "yyyyMMdd") + ".log")
Start-Transcript -Path $log -Append | Out-Null
$ok=$false
for($i=1;$i -le 3;$i++){
  try {
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\velos-run-all.ps1") -NoOpen
    $ok=$true; break
  } catch { Write-Host "[retry $i] $($_.Exception.Message)"; Start-Sleep -Seconds (10*$i) }
}
Stop-Transcript | Out-Null
if (-not $ok) { exit 1 }