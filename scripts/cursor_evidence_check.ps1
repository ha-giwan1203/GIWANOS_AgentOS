[CmdletBinding()]
param(
  [string]$Root = $(if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { "C:\giwanos" }),
  [string]$ReportPath = "",
  [int]$RecentTop = 3,
  [int]$Tail = 20
)

$ErrorActionPreference = "Stop"
$Root = [IO.Path]::GetFullPath($Root)
Set-Location $Root

function Line($s){ $script:lines.Add($s) | Out-Null }

# 수집 버킷
$lines = New-Object System.Collections.Generic.List[string]

# 헤더
Line "# VELOS Evidence Report"
Line ("- Timestamp: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Line ("- Root: {0}" -f $Root)
Line ""

# 1) Git 상태
try {
  $changed = (git status --porcelain 2>$null) -join [Environment]::NewLine
  $commit  = (git log -1 --oneline 2>$null)
  Line "## Git"
  if ($changed) {
    Line "### Changed"
    Line '```'
    Line $changed
    Line '```'
  } else {
    Line "- Working tree clean"
  }
  if ($commit) {
    Line "### Last Commit"
    Line '```'
    Line $commit
    Line '```'
  }
  Line ""
} catch { Line "## Git: unavailable" }

# 2) Health / 최신 리포트
$health = Join-Path $Root "data\reports\auto\self_check_summary.txt"
$repDir = Join-Path $Root "data\reports\auto"
$disDir = Join-Path $Root "data\reports\_dispatch"

Line "## Health"
if (Test-Path $health) {
  $he = Get-Item $health
  $age = [int]([DateTime]::UtcNow - $he.LastWriteTimeUtc).TotalSeconds
  Line ("- self_check_summary.txt: {0}  (age {1}s)" -f $he.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), $age)
} else {
  Line "- self_check_summary.txt: MISSING"
}
Line ""

# 최신 리포트/디스패치
$lastRep = $null; if (Test-Path $repDir) { $lastRep = Get-ChildItem $repDir -Filter *.md | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }
$lastDis = $null; if (Test-Path $disDir) { $lastDis = Get-ChildItem $disDir -Filter *.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 }

Line "## Latest Report/Dispatch"
Line ("- Report  : {0}" -f $(if ($lastRep) { $lastRep.FullName } else { "MISSING" }))
Line ("- Dispatch: {0}" -f $(if ($lastDis) { $lastDis.FullName } else { "MISSING" }))
Line ""

# 3) 최근 변경 상위 N 파일 + 꼬리 출력
Line "## Recent Files (Top {0})" -f $RecentTop
$recent = Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue |
          Sort-Object LastWriteTime -Descending | Select-Object -First $RecentTop

foreach ($f in $recent) {
  Line ("### {0}" -f $f.FullName)
  Line ("- Time : {0}" -f $f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))
  Line ("- Size : {0} bytes" -f $f.Length)
  try {
    Line "```"
    (Get-Content -LiteralPath $f.FullName -Tail $Tail) | ForEach-Object { Line $_ }
    Line "```"
  } catch {
    Line ("(tail error: {0})" -f $_.Exception.Message)
  }
  Line ""
}

# 4) 출력 경로 결정
if (-not $ReportPath) {
  $ReportPath = Join-Path $Root ("data\reports\auto\cursor_evidence_{0}.md" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath -Parent) | Out-Null

# 5) 저장
$enc = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($ReportPath, ($lines -join [Environment]::NewLine), $enc)
Write-Host "[OK] evidence report -> $ReportPath"