# [ACTIVE] VELOS FTS Mass Refactor Script v2 (포괄적 안전 모드)
# 기존 파일 옆에 .bak 남기고 모든 구식 참조 교체
param([string]$Root="C:\giwanos")

Write-Host "VELOS FTS Mass Refactor v2 시작..." -ForegroundColor Green
Write-Host "Root: $Root" -ForegroundColor Yellow

$targets = Get-ChildItem -Path "$Root\modules","$Root\scripts" -Recurse -Include *.py |
  Where-Object { -not $_.FullName.EndsWith(".bak") }

Write-Host "검사 대상 파일 수: $($targets.Count)" -ForegroundColor Cyan

$rules = @(
  # 기본 패턴들
  @{Pattern='(?i)\bFROM\s+memory_fts\b';              Replace='FROM memory_fts'},
  @{Pattern='(?i)\bmemory_fts\.(text_norm|text)\b';  Replace='COALESCE(m.insight, m.raw)'},
  @{Pattern='(?i)\bJOIN\s+memory_text\b';            Replace='JOIN memory'},
  @{Pattern='(?i)\bON\s+t\.rowid\s*=\s*f\.rowid\b';  Replace='ON m.id = f.rowid'},
  
  # INSERT 문 패턴들
  @{Pattern='(?i)INSERT\s+INTO\s+memory_fts\s*\(\s*rowid\s*,\s*text\s*\)';  Replace='INSERT INTO memory_fts(rowid, insight, raw)'},
  @{Pattern='(?i)INSERT\s+INTO\s+memory_fts\s*\(\s*memory_fts\s*,\s*rowid\s*,\s*text\s*\)';  Replace='INSERT INTO memory_fts(memory_fts, rowid, insight, raw)'},
  @{Pattern='(?i)INSERT\s+INTO\s+memory_fts\s*\(\s*text\s*\)';  Replace='INSERT INTO memory_fts(insight, raw)'},
  @{Pattern='(?i)INSERT\s+INTO\s+memory_fts\s*\(\s*memory_fts\s*,\s*text\s*\)';  Replace='INSERT INTO memory_fts(memory_fts, insight, raw)'},
  
  # VALUES 절 패턴들
  @{Pattern='(?i)VALUES\s*\(\s*new\.id\s*,\s*COALESCE\s*\(\s*new\.insight\s*,\s*new\.raw\s*,\s*''\s*\)\s*\)';  Replace='VALUES (new.id, COALESCE(new.insight, new.raw, ''''), COALESCE(new.insight, new.raw, ''''))'},
  @{Pattern='(?i)VALUES\s*\(\s*old\.id\s*,\s*COALESCE\s*\(\s*old\.insight\s*,\s*old\.raw\s*,\s*''\s*\)\s*\)';  Replace='VALUES (old.id, COALESCE(old.insight, old.raw, ''''), COALESCE(old.insight, old.raw, ''''))'},
  
  # CREATE TABLE 패턴
  @{Pattern='(?i)CREATE\s+VIRTUAL\s+TABLE\s+.*memory_fts.*USING\s+fts5\s*\(\s*text\s*\)';  Replace='CREATE VIRTUAL TABLE memory_fts USING fts5(insight, raw)'},
  
  # SELECT 문에서 text 컬럼 참조
  @{Pattern='(?i)SELECT.*text.*FROM\s+memory_fts';  Replace='SELECT insight, raw FROM memory_fts'},
  @{Pattern='(?i)WHERE.*text\s+LIKE';  Replace='WHERE insight LIKE'},
  
  # COALESCE 패턴 개선
  @{Pattern='(?i)COALESCE\s*\(\s*t\.text_norm\s*,\s*m\.insight\s*,\s*m\.raw\s*\)';  Replace='COALESCE(m.insight, m.raw)'}
)

$modifiedCount = 0

foreach($f in $targets){
  $orig = Get-Content $f.FullName -Raw -Encoding UTF8
  $new  = $orig
  $fileModified = $false
  
  foreach($r in $rules){ 
    if($new -match $r.Pattern) {
      $new = [regex]::Replace($new, $r.Pattern, $r.Replace)
      $fileModified = $true
    }
  }
  
  if($fileModified){
    # 백업 생성
    Copy-Item $f.FullName "$($f.FullName).bak" -Force
    Set-Content -Encoding UTF8 $f.FullName $new
    Write-Host "[patched] $($f.FullName)" -ForegroundColor Green
    $modifiedCount++
  }
}

Write-Host "`n=== FTS Mass Refactor v2 완료 ===" -ForegroundColor Green
Write-Host "수정된 파일 수: $modifiedCount" -ForegroundColor Yellow
Write-Host "백업 파일은 .bak 확장자로 생성됨" -ForegroundColor Cyan
