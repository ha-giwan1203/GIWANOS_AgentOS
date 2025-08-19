# [ACTIVE] VELOS FTS Mass Refactor Script (안전 모드)
# 기존 파일 옆에 .bak 남기고 매치만 교체
param([string]$Root="C:\giwanos")

Write-Host "VELOS FTS Mass Refactor 시작..." -ForegroundColor Green
Write-Host "Root: $Root" -ForegroundColor Yellow

$targets = Get-ChildItem -Path "$Root\modules","$Root\scripts" -Recurse -Include *.py |
  Where-Object { -not $_.FullName.EndsWith(".bak") }

Write-Host "검사 대상 파일 수: $($targets.Count)" -ForegroundColor Cyan

$rules = @(
  @{Pattern='(?i)\bFROM\s+memory_fts\b';              Replace='FROM memory_fts'},
  @{Pattern='(?i)\bmemory_fts\.(text_norm|text)\b';  Replace='COALESCE(m.insight, m.raw)'},
  @{Pattern='(?i)\bJOIN\s+memory_text\b';            Replace='JOIN memory'},
  @{Pattern='(?i)\bON\s+t\.rowid\s*=\s*f\.rowid\b';  Replace='ON m.id = f.rowid'}
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

Write-Host "`n=== FTS Mass Refactor 완료 ===" -ForegroundColor Green
Write-Host "수정된 파일 수: $modifiedCount" -ForegroundColor Yellow
Write-Host "백업 파일은 .bak 확장자로 생성됨" -ForegroundColor Cyan
