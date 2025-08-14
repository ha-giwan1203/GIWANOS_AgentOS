$ErrorActionPreference = "Stop"
$root = "C:\giwanos"
$log  = Join-Path $root ("data\\logs\\ts_evidence_" + (Get-Date -Format "yyyyMMdd") + ".log")
Start-Transcript -Path $log -Append | Out-Null
try {
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "scripts\\cursor_evidence_check.ps1")
  $code = $LASTEXITCODE
} catch { $code = 1; Write-Host "[ERR] $($_.Exception.Message)" -ForegroundColor Red }
Stop-Transcript | Out-Null
exit $code
