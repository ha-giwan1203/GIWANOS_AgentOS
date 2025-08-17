# [ACTIVE] VELOS 자동 정리 워처
# 파일 생성/수정/이동을 감지해서 velos_cleanup.ps1를 디바운스 호출

param(
  [int]$DebounceMs = 1500
)

$ErrorActionPreference = 'SilentlyContinue'
$root   = "C:\giwanos"
$script = Join-Path $root "scripts\velos_cleanup.ps1"

if (-not (Test-Path $script)) {
  Write-Host "[WARN] cleanup 스크립트가 없어 종료: $script"
  exit 0
}

# 감시 대상 확장자
$filter = '*.ps1','*.py','*.json','*.yaml','*.yml','*.cfg','*.ini','*.bat','*.vbs'
$paths  = @(
  "$root\scripts",
  "$root\experiments",
  "$root\modules",
  "$root\configs",
  "$root"  # 루트 흩어진 잡동사니도 감지
)

# 디바운스 타이머
$pending = $false
$timer = New-Object System.Timers.Timer
$timer.Interval = $DebounceMs
$timer.AutoReset = $false
$timer.add_Elapsed({
  $pending = $false
  try {
    Start-Process pwsh -WindowStyle Hidden -ArgumentList @(
      '-NoProfile','-ExecutionPolicy','Bypass','-File',$script
    ) | Out-Null
  } catch {}
})

$handlers = @()

function Hook($fsw){
  $action = {
    if (-not $script) { return }
    $global:pending = $true
    $global:timer.Stop()
    $global:timer.Start()
  }
  $handlers += Register-ObjectEvent $fsw Changed -Action $action
  $handlers += Register-ObjectEvent $fsw Created -Action $action
  $handlers += Register-ObjectEvent $fsw Renamed -Action $action
  $handlers += Register-ObjectEvent $fsw Deleted -Action $action
}

$watchers = @()
foreach ($p in $paths) {
  if (-not (Test-Path $p)) { continue }
  foreach ($f in $filter) {
    $fsw = New-Object System.IO.FileSystemWatcher
    $fsw.Path = $p
    $fsw.Filter = $f
    $fsw.IncludeSubdirectories = $true
    $fsw.EnableRaisingEvents = $true
    Hook $fsw
    $watchers += $fsw
  }
}

Write-Host "[OK] AutoClean watcher started. Ctrl+C로 종료."
# 백그라운드 대기
while ($true) { Start-Sleep 5 }
