# [ACTIVE] velos_cleanup.ps1
param(
  [int]$LogDays = 30,      # logs 보관일
  [int]$ReportDays = 90,   # reports 보관일
  [int]$ExperimentsDays = 30,  # experiments를 archive로 보내는 기준
  [int]$ArchivePurgeDays = 180 # archive에서 완전 삭제
)

$ErrorActionPreference = 'Stop'
$root  = "C:\giwanos"
$today = Get-Date -Format 'yyyyMMdd'
$arc   = Join-Path $root "archive\$today"
New-Item -ItemType Directory -Path $arc -Force | Out-Null

# 2-1. 오래된 로그/리포트 정리
Get-ChildItem "$root\data\logs" -File -ErrorAction SilentlyContinue |
  ? { $_.LastWriteTime -lt (Get-Date).AddDays(-$LogDays) } |
  Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem "$root\data\reports" -File -ErrorAction SilentlyContinue |
  ? { $_.LastWriteTime -lt (Get-Date).AddDays(-$ReportDays) } |
  Remove-Item -Force -ErrorAction SilentlyContinue

# 2-2. 루트의 잡파일을 archive로 이동
Get-ChildItem $root -File -ErrorAction SilentlyContinue |
  ? { $_.Extension -in '.log','.tmp','.bak','.old' } |
  Move-Item -Destination $arc -Force -ErrorAction SilentlyContinue

# 2-3. experiments 자동 아카이브(오래된 실험물)
Get-ChildItem "$root\experiments" -File -ErrorAction SilentlyContinue |
  ? { $_.LastWriteTime -lt (Get-Date).AddDays(-$ExperimentsDays) } |
  Move-Item -Destination $arc -Force -ErrorAction SilentlyContinue

# 2-4. archive 장기 보관물 삭제
Get-ChildItem "$root\archive" -Recurse -File -ErrorAction SilentlyContinue |
  ? { $_.LastWriteTime -lt (Get-Date).AddDays(-$ArchivePurgeDays) } |
  Remove-Item -Force -ErrorAction SilentlyContinue

# 2-5. 주석 태그 기반 분류 보정
# [ACTIVE] → scripts로, [EXPERIMENT] → experiments로
$scan = Get-ChildItem $root -Recurse -File -Include *.ps1,*.py -ErrorAction SilentlyContinue
foreach($f in $scan){
  $head = (Get-Content $f.FullName -TotalCount 1 -ErrorAction SilentlyContinue) -as [string]
  if($head -match '^\s*#\s*\[ACTIVE\]'){
    $dest = Join-Path "$root\scripts" $f.Name
    if($f.FullName -ne $dest){ Copy-Item $f.FullName $dest -Force }
  } elseif($head -match '^\s*#\s*\[EXPERIMENT\]'){
    $dest = Join-Path "$root\experiments" $f.Name
    if($f.FullName -ne $dest){ Copy-Item $f.FullName $dest -Force }
  }
}

Write-Host "[OK] 정리 완료"
