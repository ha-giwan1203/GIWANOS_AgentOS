[CmdletBinding()]
param(
  [string]$Message = "chore(sync): VELOS autofix + self_check pass",
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSCommandPath -Parent) | Out-Null
Set-Location (Join-Path (Get-Location) "..")  # go project root

function Die($m){ Write-Host "[velos-sync][FAIL] $m" -ForegroundColor Red; exit 1 }
function Info($m){ Write-Host "[velos-sync] $m" }

# 1) 사전 점검
Info "running self_check..."
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\tools\self_check.ps1" | Out-Null

# 2) git 상태
try { git rev-parse --is-inside-work-tree | Out-Null } catch { Die "여긴 git 저장소가 아님" }
git add -A

# 3) .env가 스테이징 됐는지 마지막 방어
$leaks = git diff --cached --name-only | Select-String -Pattern "configs\/\.env$|\.env$"
if ($leaks) { Die ".env가 커밋에 포함됨. .gitignore 확인하고 unstaged 하셈." }

# 4) 변경 없으면 종료
$staged = git diff --cached --name-only
if (-not $staged) { Info "변경 사항 없음. 종료."; exit 0 }

# 5) 커밋
Info "commit..."
git commit -m $Message

# 6) 푸시
if (-not $NoPush) {
  Info "push..."
  git push
  Info "done."
} else {
  Info "push 생략(NoPush)"
}