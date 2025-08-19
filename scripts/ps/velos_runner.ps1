# [ACTIVE] VELOS 운영 철학 선언문
#Requires -Version 7
param(
  [string]$VELOS_ROOT = "C:\giwanos",
  [string]$DB_PATH_REL = "data\velos.db",
  [string]$PY = "python"
)
# 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference = "Stop"
trap { Write-Error $_; exit 1 }
function Log([string]$m){ $ts=(Get-Date).ToString("HH:mm:ss"); Write-Host "[$ts] $m" }

# Paths
$DB = Join-Path $VELOS_ROOT $DB_PATH_REL
$SQL = Join-Path $VELOS_ROOT "scripts\sql\fts_lockin_ext.sql"
$PYDIR = Join-Path $VELOS_ROOT "scripts\py"
$BKDIR = Join-Path $VELOS_ROOT "backup"      # 실제 폴더명
$ADAPTER = Join-Path $VELOS_ROOT "modules\utils\memory_adapter.py"
$SCHED = Join-Path $VELOS_ROOT "scripts\velos_master_scheduler.py"

if(!(Test-Path $BKDIR)){ New-Item -ItemType Directory -Path $BKDIR | Out-Null }

# SQL 스키마 파일 무결성 검증
$expected = Get-Content "C:\giwanos\scripts\sql\fts_lockin_ext.sha256"
$actual   = (Get-FileHash "C:\giwanos\scripts\sql\fts_lockin_ext.sql" -Algorithm SHA256).Hash
if($expected -ne $actual){ throw "fts_lockin_ext.sql tampered" }

# Sanity
if(!(Test-Path $DB)){ throw "DB not found: $DB" }
if(!(Test-Path $SQL)){ throw "SQL not found: $SQL" }
Log "VELOS_DB_PATH=$DB"

# Backup
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$bk = Join-Path $BKDIR "velos_${stamp}.bench.db"
Copy-Item $DB $bk -Force
Log "Backup created: $bk"

# FTS lock-in
$env:VELOS_DB_PATH = $DB
Set-Location $PYDIR
Log "Running run_fts_lockin.py"
& $PY "run_fts_lockin.py" 2>&1 | Write-Host

# Smoke test with validation
Log "Running fts_smoke_test.py"
$smoke = & $PY "fts_smoke_test.py" 2>&1
Write-Host $smoke
if($smoke -notmatch "alpha_after_update=0" -or $smoke -notmatch "after_delete=0"){
  throw "FTS smoke failed: $smoke"
}

# MemoryAdapter 점검
if(Test-Path $ADAPTER){
  $content = Get-Content $ADAPTER -Raw
  if($content -notmatch "FROM\s+memory_fts\s+f\s+JOIN\s+memory\s+m\s+ON\s+m\.id\s*=\s*f\.rowid"){
    Log "WARN: MemoryAdapter 검색 쿼리 미적용. 자동 교정 시도."
    Copy-Item $ADAPTER "$ADAPTER.bak" -Force
    $content = $content -replace '(?s)SELECT.+?LIMIT\s*\?;','SELECT m.id, m.ts, m.role, m.insight, m.raw
      FROM memory_fts f
      JOIN memory m ON m.id = f.rowid
      WHERE memory_fts MATCH ?
      ORDER BY m.ts DESC
      LIMIT ?;'
    Set-Content -Encoding UTF8 $ADAPTER $content
    Log "MemoryAdapter 교정 완료. 백업: $ADAPTER.bak"
  } else {
    Log "MemoryAdapter 검색 쿼리 OK."
  }
} else {
  Log "WARN: $ADAPTER 없음. 스킵."
}

# 스케줄러 스모크 (선택)
if(Test-Path $SCHED){
  Set-Location (Split-Path $SCHED -Parent)
  Log "Scheduler dry-run import"
  & $PY -c "import runpy; runpy.run_path(r'$SCHED', run_name='__main__')" 2>&1 | Write-Host
} else {
  Log "INFO: velos_master_scheduler.py 없음? 경로 다시 확인 필요."
}

Log "Runner completed."
