param(
  [string]$ReportPath,              # 막 생성된 .md 경로(없으면 최신파일 자동 탐색)
  [switch]$NoPush,                  # 푸시 생략 옵션
  [switch]$NoOpen                   # Cursor로 열기 생략 옵션
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot; Set-Location (Join-Path $PWD "..")

# 1) 최신 리포트 탐색
if (-not $ReportPath -or -not (Test-Path $ReportPath)) {
  $dir = "C:\giwanos\data\reports\auto"
  if (-not (Test-Path $dir)) { throw "auto reports dir not found: $dir" }
  $ReportPath = Get-ChildItem $dir -Filter *.md | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -Expand FullName
  if (-not $ReportPath) { throw "no report found in $dir" }
}
Write-Host "[postrun] report: $ReportPath"

# 2) git 커밋/푸시
if (-not $NoPush) {
  try {
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\scripts\git_auto_sync.ps1" -IncludeMemory -Message "report: $(Split-Path $ReportPath -Leaf)" | Out-Null
    Write-Host "[postrun] git sync done"
  } catch {
    Write-Host "[postrun][WARN] git sync failed: $($_.Exception.Message)"
  }
} else {
  Write-Host "[postrun] push skipped"
}

# 3) Cursor 실행파일 추정 경로
$cursorPaths = @(
  "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe",
  "$env:USERPROFILE\AppData\Local\Programs\Cursor\Cursor.exe"
) | Where-Object { Test-Path $_ }

# 4) Cursor로 파일 열기(있으면)
if (-not $NoOpen -and $cursorPaths.Count -gt 0) {
  $exe = $cursorPaths[0]
  try {
    Start-Process -FilePath $exe -ArgumentList "`"$ReportPath`"" -WindowStyle Normal
    Write-Host "[postrun] opened in Cursor: $exe"
  } catch {
    Write-Host "[postrun][WARN] open in Cursor failed: $($_.Exception.Message)"
  }
} else {
  Write-Host "[postrun] Cursor not found or NoOpen"
}