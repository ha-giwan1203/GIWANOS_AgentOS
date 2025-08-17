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
  [string]$Message = "chore(auto-sync): VELOS changes",
  [switch]$NoPush,
  [switch]$IncludeMemory,     # 기본 제외인 data/memory 포함하고 싶을 때만 사용
  [int]$TimeoutPush = 120     # git push 타임아웃(초)
)
$ErrorActionPreference = "Stop"

# 레포 루트로
Set-Location (Split-Path $PSCommandPath -Parent) | Out-Null
Set-Location (Join-Path (Get-Location) "..")  # -> repo root

function Info($m){ Write-Host "[auto-sync] $m" }
function Warn($m){ Write-Host "[auto-sync][WARN] $m" -ForegroundColor Yellow }
function Die($m){ Write-Host "[auto-sync][FAIL] $m" -ForegroundColor Red; exit 1 }

try { git rev-parse --is-inside-work-tree | Out-Null } catch { Die "여긴 git 저장소가 아님" }

# 제외 패턴: 잡음은 커밋 금지
$exclude = @(
  '^logs/.*',
  '^data/reports/_dispatch/.*',
  '^__pycache__/.*','.*\.pyc$','.*\.pyo$',
  '^.*\.tmp$','^.*\.temp$','^.*\.bak$','^.*\.backup$','^.*\.orig$'
)
if (-not $IncludeMemory) { $exclude += '^data/memory/.*' }

function Get-Eligible {
  $raw = git status --porcelain=1
  if (-not $raw) { return @() }
  $files=@()
  foreach($line in $raw){
    $p = $line.Trim() -replace '^[ MARC?U]{1,2}\s+',''
    if (-not $p) { continue }
    $u = $p -replace '\\','/'
    $skip = $false
    foreach($rx in $exclude){ if ($u -match $rx){ $skip=$true; break } }
    if (-not $skip){ $files += $p }
  }
  $files | Sort-Object -Unique
}

$files = Get-Eligible
if (-not $files -or $files.Count -eq 0) { Info "변경 없음. 종료."; exit 0 }

Info ("스테이징 {0}개" -f $files.Count)
git add -- "-- $files"

# pre-commit 훅이 self_check/민감파일을 자동 차단함
$tag = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
try {
  git commit -m "$Message ($tag)" | Out-Null
  Info "commit 완료"
} catch {
  Warn "커밋 실패: $($_.Exception.Message)"; exit 0
}

if ($NoPush) { Info "push 생략(-NoPush)"; exit 0 }

# push 타임아웃 처리
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "git"
$psi.Arguments = "push"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$p = New-Object System.Diagnostics.Process
$p.StartInfo = $psi
[void]$p.Start()
if (-not $p.WaitForExit($TimeoutPush*1000)) {
  try { $p.Kill() } catch {}
  Warn "push 타임아웃(${TimeoutPush}s). 다음 회차에 재시도."
  exit 0
}
if ($p.ExitCode -ne 0) {
  $err = $p.StandardError.ReadToEnd()
  Warn ("push 실패(exit {0}): {1}" -f $p.ExitCode, ($err -replace '\s+',' '))
} else {
  Info "push 완료"
}
