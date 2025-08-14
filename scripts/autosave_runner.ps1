[CmdletBinding()] param([int]$DebounceMs=1500)
$ErrorActionPreference="Stop"
$ROOT = "C:\giwanos"
$LOCK = Join-Path $ROOT "data\logs\run.lock"
$LOG  = Join-Path $ROOT ("data\logs\autosave_runner_{0}.log" -f (Get-Date -Format yyyyMMdd))
$script:lastRun = 0

function Log($m){ "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"),$m | Out-File -FilePath $LOG -Append -Encoding UTF8 }

function KickRun([string]$reason,[string]$path){
  $now=[Environment]::TickCount64
  if ($now - $script:lastRun -lt $DebounceMs){ return }
  if (Test-Path $LOCK){ Log "skip(lock): $reason :: $path"; return }
  try {
    New-Item -ItemType File -Path $LOCK -Force | Out-Null
    Log "preflight... ($reason :: $path)"
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\preflight_quickcheck.ps1" 2>$null
    if ($LASTEXITCODE -ne 0){ Log "preflight FAIL ($reason)"; return }
    Log "run start"
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos-run-all.ps1" -NoOpen
    Log "run done"
  } catch {
    Log ("ERROR: {0}" -f $_.Exception.Message)
  } finally {
    Remove-Item $LOCK -Force -ErrorAction SilentlyContinue
    $script:lastRun = [Environment]::TickCount64
  }
}

# ===== Watcher =====
$watchRoots = @("$ROOT")
$filters    = @("*.py","*.ps1","*.json")

foreach($wr in $watchRoots){
  $fsw = New-Object IO.FileSystemWatcher $wr, "*.*"
  $fsw.IncludeSubdirectories = $true
  $fsw.EnableRaisingEvents  = $true
  $fsw.NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite, Size'

  Register-ObjectEvent $fsw Changed -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Changed :: $p";  KickRun "Changed" $p
  } | Out-Null
  Register-ObjectEvent $fsw Created -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Created :: $p";  KickRun "Created" $p
  } | Out-Null
  Register-ObjectEvent $fsw Renamed -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Renamed :: $p";  KickRun "Renamed" $p
  } | Out-Null
}

"[{0}] watch start" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $LOG -Append -Encoding UTF8
while($true){ Start-Sleep -Milliseconds 400 }