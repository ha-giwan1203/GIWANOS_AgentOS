# C:\giwanos\scripts\run_healthcheck.ps1
$ErrorActionPreference = 'Stop'
$root  = 'C:\giwanos'
$logDir = Join-Path $root 'data\logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logOut = Join-Path $logDir "healthcheck_$stamp.log"
$logErr = Join-Path $logDir "healthcheck_$stamp.err"

$script = 'C:\giwanos\scripts\velos_health_check.ps1'

$ps = Start-Process powershell.exe -NoNewWindow -PassThru -Wait `
  -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$script`"") `
  -RedirectStandardOutput $logOut -RedirectStandardError $logErr

# 에러 로그를 본 로그에 덧붙이고 .err 삭제
if ((Test-Path $logErr) -and (Get-Item $logErr).Length -gt 0) {
  Get-Content $logErr | Add-Content $logOut
  Remove-Item $logErr -Force
}

exit $ps.ExitCode
