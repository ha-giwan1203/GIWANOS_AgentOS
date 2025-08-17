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
