[CmdletBinding()]
param(
  [string]$ReportPath,        # 최근 생성된 .md 경로 (없으면 자동 탐색)
  [switch]$NoPush,            # Git 푸시 생략
  [switch]$NoOpen             # Cursor로 열기 생략
)

$ErrorActionPreference = "Stop"

# 루트 고정
$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$ROOT = [IO.Path]::GetFullPath($ROOT)

# 프로젝트 루트로 이동
Set-Location -Path $ROOT

function Info($m){ Write-Host "[postrun] $m" }
function Warn($m){ Write-Host "[postrun][WARN] $m" -ForegroundColor Yellow }

# 1) 최신 리포트 탐색
if (-not $ReportPath -or -not (Test-Path $ReportPath)) {
  $dir = Join-Path $ROOT "data\reports\auto"
  if (-not (Test-Path $dir)) { throw "auto reports dir not found: $dir" }
  $last = Get-ChildItem $dir -Filter *.md | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $last) { throw "no report found in $dir" }
  $ReportPath = $last.FullName
}
Info "report: $ReportPath"

# 2) Git 커밋/푸시 (민감파일 보호는 git_auto_sync.ps1에서 처리됨)
if (-not $NoPush) {
  try {
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass `
      -File (Join-Path $ROOT "scripts\git_auto_sync.ps1") `
      -IncludeMemory -Message "report: $(Split-Path $ReportPath -Leaf)" | Out-Null
    Info "git sync done"
  } catch {
    Warn "git sync failed: $($_.Exception.Message)"
  }
} else {
  Info "push skipped"
}

# 3) Cursor 실행파일 후보
$cursorPaths = @(
  "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe",
  "$env:USERPROFILE\AppData\Local\Programs\Cursor\Cursor.exe"
) | Where-Object { Test-Path $_ }

# 4) Cursor로 파일 열기
if (-not $NoOpen -and $cursorPaths.Count -gt 0) {
  $exe = $cursorPaths[0]
  try {
    Start-Process -FilePath $exe -ArgumentList "`"$ReportPath`"" -WindowStyle Normal
    Info "opened in Cursor: $exe"
  } catch {
    Warn "open in Cursor failed: $($_.Exception.Message)"
  }
} else {
  Info "Cursor not found or NoOpen"
}
