# [ACTIVE] VELOS 라벨 검사 스크립트
$root = "C:\giwanos"
$all = Get-ChildItem $root -Recurse -File -Include *.ps1,*.py | Where-Object { 
  $_.FullName -notmatch '\\.venv_link\\' -and 
  $_.FullName -notmatch '\\.venv\\' -and
  $_.FullName -notmatch '\\__pycache__\\' -and
  $_.FullName -notmatch '\\.git\\'
}
$untagged = @()
$misplaced = @()

foreach ($f in $all) {
  $head = (Get-Content $f.FullName -TotalCount 1 -ErrorAction SilentlyContinue) -as [string]
  if ($head -notmatch '^\s*#\s*\[(ACTIVE|EXPERIMENT)\]') { $untagged += $f; continue }
  if ($head -match '\[ACTIVE\]' -and $f.FullName -notmatch '\\scripts\\') { $misplaced += $f }
  if ($head -match '\[EXPERIMENT\]' -and $f.FullName -notmatch '\\experiments\\') { $misplaced += $f }
}

Write-Host "=== 라벨 누락 ==="
$untagged | Select FullName
Write-Host "`n=== 위치 오류(라벨과 폴더 불일치) ==="
$misplaced | Select FullName
