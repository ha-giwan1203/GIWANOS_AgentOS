[CmdletBinding()] param([switch]$Once,[switch]$NoGit)
$ErrorActionPreference = "Stop"

Import-Module (Join-Path (Get-Location) "tools\velos.common.psm1") -Force

$ROOT = Get-VelosRoot
Set-Location $ROOT
$logs = Join-Path $ROOT "data\logs"
$autofixLog = Join-Path $logs "autofix.log"
Ensure-Dirs -Paths @($logs)

$log = New-VelosLogger -Name "velos-run" -LogPath $autofixLog

if(-not $NoGit){
  try { git config core.autocrlf input | Out-Null; git status --porcelain | Out-Null }
  catch { $log.Warn("Git unavailable; continuing.") }
}

function Invoke-VelosOnce{
  $py="python"; $script=Join-Path $ROOT "scripts\run_giwanos_master_loop.py"
  $env:PYTHONPATH=$ROOT
  $log.Info("start")
  try{
    $out = & $py $script 2>&1
    $code=$LASTEXITCODE
    if($code -ne 0){
      $out | Out-File -FilePath (Join-Path $logs "last_run.stderr.txt") -Encoding UTF8
      $log.Error(("python exit={0}" -f $code))
      throw "Master loop returned non-zero $code"
    } else {
      $out | Out-File -FilePath (Join-Path $logs "last_run.stdout.txt") -Encoding UTF8
      $log.Info("success")
    }
  } catch {
    $log.Error($_.Exception.Message)
    throw
  } finally {
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "tools\self_check.ps1") | Out-Null
  }
}

if($Once){ Invoke-VelosOnce; exit 0 }
while($true){ try{ Invoke-VelosOnce } catch { $log.Warn($_) }; Start-Sleep -Seconds 300 }