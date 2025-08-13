param(
  [string]$Room="roomA",
  [string]$User="local"
)
$ErrorActionPreference="Stop"
$py="C:\Users\User\venvs\velos\Scripts\python.exe"

# 0. 브리지 헬스
& $py C:\giwanos\scripts\velos_bridge.py --probe | Out-Null

# 1. 테스트 메시지 투입
$idem="smoke-"+(Get-Date -f yyyyMMddHHmmss)
$env:VELOS_ALLOW_BRIDGE="1"
& $py C:\giwanos\scripts\velos_bridge.py --ingest "pipeline_smoke_$([guid]::NewGuid())" --idempotency $idem --room $Room --user $User
$env:VELOS_ALLOW_BRIDGE=$null

# 2. 스케줄 플러시 1회(태스크 실패시 수동 플러시로 폴백)
try { schtasks /run /tn "VELOS Bridge Flush" 2>$null; Start-Sleep 3 } catch { & $py C:\giwanos\scripts\velos_bridge.py }

# 3. 마스터 루프 프리체크/드라이런
& $py C:\giwanos\scripts\run_giwanos_master_loop.py --precheck
& $py C:\giwanos\scripts\run_giwanos_master_loop.py --dry-run

# 4. 멱등키 반영 확인
& $py -c "import sqlite3;con=sqlite3.connect(r'C:\giwanos\data\velos.db');print('IDEMP_COUNT=',con.execute('select count(*) from messages where idempotency_key=?',(r'$idem',)).fetchone()[0]);con.close()"
Write-Host "`n[HEALTH]" -ForegroundColor Cyan
Get-Content C:\giwanos\data\logs\system_health.json -Raw | Write-Output


