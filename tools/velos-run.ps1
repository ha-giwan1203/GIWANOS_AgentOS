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
  $env:PYTHONPATH="$ROOT;$ROOT\modules"
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

# auto: sync changes to remote
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\scripts\git_auto_sync.ps1" -Message "auto-sync: after velos-run"


# === auto-generate: create timestamped report & index ===
$env:PYTHONPATH = "$ROOT;$ROOT\modules"
try {
  python ".\scripts\auto_generate_runner.py" | Out-Null
  Write-Host "[auto-generate] ok"
} catch {
  Write-Host "[auto-generate] skipped: $($_.Exception.Message)"
}


# === auto-generate: create timestamped report & index (hardened) ===
try {
  $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not $Python) { $Python = (Get-Command py -ErrorAction SilentlyContinue).Source }
  if (-not $Python) { throw "python not found in PATH" }

  Push-Location $ROOT
  $env:PYTHONPATH = "$ROOT;$ROOT\modules"
  $pinfo = New-Object System.Diagnostics.ProcessStartInfo
  $pinfo.FileName = $Python
  $pinfo.Arguments = ".\scripts\auto_generate_runner.py"
  $pinfo.WorkingDirectory = $ROOT
  $pinfo.UseShellExecute = $false
  $pinfo.RedirectStandardOutput = $true
  $p = [System.Diagnostics.Process]::Start($pinfo)
  $null = $p.WaitForExit(60*1000)
  if ($p.HasExited -and $p.ExitCode -eq 0) {
    Write-Host "[auto-generate] ok"
  } else {
    Write-Host "[auto-generate][WARN] exit=$($p.ExitCode)"
  }
} catch {
  Write-Host "[auto-generate][FAIL] $($_.Exception.Message)"
} finally {
  Pop-Location
}


# [postrun] report:
try {
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\tools\velos-postrun.ps1"
} catch { Write-Host "[postrun][WARN] " }

