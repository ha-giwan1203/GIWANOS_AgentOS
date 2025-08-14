[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$Message = "chore(auto): commit tracked changes",
  [switch]$NoPush,                # 푸시 생략
  [switch]$Watch,                 # 감시 모드(변경 생기면 자동 커밋)
  [int]$Interval = 15,            # 감시 주기(초)
  [switch]$IncludeMemory          # 기본 제외 대상 중 data/memory 포함하고 싶을 때
)

$ErrorActionPreference = "Stop"
$root = [IO.Path]::GetFullPath($(if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { "C:\giwanos" }))
Set-Location $root

function Info($m){ Write-Host "[autocommit] $m" }
function Warn($m){ Write-Host "[autocommit][WARN] $m" -ForegroundColor Yellow }
function Die($m){ Write-Host "[autocommit][FAIL] $m" -ForegroundColor Red; exit 1 }

# git 저장소 확인
try { git rev-parse --is-inside-work-tree | Out-Null } catch { Die "여긴 git 저장소가 아님: $root" }

# 제외 패턴(변경은 되지만 커밋 원치 않는 것들)
$exclude = @(
  '^logs/.*',
  '^data/reports/_dispatch/.*',
  '^__pycache__/.*','.*\.pyc$','.*\.pyo$',
  '^tools/.*\.log$'
)
if (-not $IncludeMemory) { $exclude += '^data/memory/.*' }  # 필요시 -IncludeMemory로 허용

function Get-EligibleChanges {
  $raw = git status --porcelain=1
  if (-not $raw) { return @() }
  $files = @()
  foreach($line in $raw){
    # 라인 예: " M modules/core/velos_command_processor.py"
    $p = $line.Trim() -replace '^[ MARC?U]{1,2}\s+',''
    if (-not $p) { continue }
    $unix = $p -replace '\\','/'
    $skip = $false
    foreach($rx in $exclude){ if ($unix -match $rx){ $skip = $true; break } }
    if (-not $skip){ $files += $p }
  }
  return $files | Sort-Object -Unique
}

function Do-Once {
  $files = Get-EligibleChanges
  if (-not $files -or $files.Count -eq 0) { Info "변경 없음(커밋 생략)"; return $false }

  Info ("스테이징 대상 {0}개" -f $files.Count)
  git add -- $files

  # pre-commit 훅에서 self_check 실패/ .env 포함 등은 자동 차단됨
  $msg = "{0} ({1:yyyy-MM-dd HH:mm:ss})" -f $Message, (Get-Date)
  try {
    git commit -m $msg | Out-Null
  } catch {
    Warn "커밋 실패: $($_.Exception.Message)"
    return $false
  }

  if (-not $NoPush) {
    try {
      Info "push..."
      git push | Out-Null
      Info "done."
    } catch {
      Warn "push 실패: $($_.Exception.Message)"
    }
  } else {
    Info "push 생략(-NoPush)"
  }
  return $true
}

if (-not $Watch) {
  Do-Once | Out-Null
  exit 0
}

# 감시 모드
Info ("감시 모드 시작: {0}s 간격" -f $Interval)
$lastHash = git rev-parse HEAD
while ($true) {
  try {
    $changed = Get-EligibleChanges
    if ($changed -and $changed.Count -gt 0) {
      Info ("감지됨 → {0}개" -f $changed.Count)
      if (Do-Once) { $lastHash = git rev-parse HEAD }
    }
  } catch {
    Warn "루프 오류: $($_.Exception.Message)"
  }
  Start-Sleep -Seconds $Interval
}