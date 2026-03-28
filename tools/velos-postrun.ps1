# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
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
