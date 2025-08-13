$DefaultRoot = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")) }
param(
  [string[]]$Tasks = @("VELOS Bridge Flush","VELOS Daily Report","VELOS DB Backup"),
  [switch]$RunFlushNow  # 지정하면 Flush 태스크를 즉시 1회 실행해줌
)

$ErrorActionPreference = "Stop"

function HL($t){ Write-Host $t -ForegroundColor Cyan }

# --- 0. 환경/경로 ---
$health = Join-Path $root "data\logs\system_health.json"
$bkdir  = Join-Path $root "data\backups"
$rpdir  = Join-Path $root "data\reports"
$opslog = Join-Path $root "data\logs\ops_patch_log.jsonl"

# --- 1. 스케줄 태스크 상태 ---
HL "`n=== Scheduled Tasks ==="
foreach($t in $Tasks){
  try{
    $raw = schtasks /query /tn $t /v /fo LIST 2>&1 | Out-String
    if($LASTEXITCODE -ne 0){ Write-Host "[$t] query failed: $raw" -ForegroundColor Yellow }
    else{
      # 핵심 라인만 추려서 보기 좋게
      $lines = $raw -split "`r?`n" | Where-Object {
        $_ -match '^(TaskName:|Next Run Time:|Last Run Time:|Last Result:|Task To Run:|Run As User:)'
      }
      Write-Host "[$t]"
      $lines | ForEach-Object { "  $_" } | Write-Output
    }
  }catch{
    Write-Host "[$t] error: $_" -ForegroundColor Yellow
  }
}

# --- 2. 옵션: Flush 즉시 1회 실행 ---
if($RunFlushNow){
  HL "`n=== Run: VELOS Bridge Flush (once) ==="
  try{
    schtasks /run /tn "VELOS Bridge Flush" 2>$null
    Start-Sleep -Seconds 3
    Write-Host "Triggered." -ForegroundColor Green
  }catch{
    Write-Host "Trigger failed: $_" -ForegroundColor Yellow
  }
}

# --- 3. Bridge Health ---
HL "`n=== Bridge Health ==="
if(Test-Path $health){ Get-Content $health -Raw } else { Write-Host "(no health file)" -ForegroundColor Yellow }

# --- 4. 최근 산출물(백업/리포트) ---
HL "`n=== Latest Artifacts ==="
if(Test-Path $bkdir){
  $b = Get-ChildItem $bkdir -File | Sort-Object LastWriteTime -Desc | Select-Object -First 1
  if($b){ "Backup : {0} ({1} KB)" -f $b.Name, [int]([math]::Round($b.Length/1KB)) }
  else{ "(no backups yet)" }
}else{ "(backups dir missing)" }

if(Test-Path $rpdir){
  $r = Get-ChildItem $rpdir -File | Sort-Object LastWriteTime -Desc | Select-Object -First 1
  if($r){ "Report : {0} ({1} KB)" -f $r.Name, [int]([math]::Round($r.Length/1KB)) }
  else{ "(no reports yet)" }
}else{ "(reports dir missing)" }

# --- 5. ops 로그 꼬리 ---
HL "`n=== ops_patch_log.jsonl tail(10) ==="
if(Test-Path $opslog){ Get-Content $opslog -Tail 10 -ErrorAction SilentlyContinue } else { "(no ops log)" }

# 끝











