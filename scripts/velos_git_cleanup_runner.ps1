# VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

<# ======================================================================
 VELOS Git 저장소 정리 실행 도우미
 - 다양한 실행 모드를 제공하는 래퍼 스크립트
 - 실행 전 사전 점검 및 환경 설정 자동화
 ====================================================================== #>

[CmdletBinding()]
param(
    [string]$CommitMessage = "chore: pre-commit excludes + normalize EOL + ignore volatile outputs",
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help
)

# 환경 변수에서 VELOS_ROOT 경로 로드
$velosRoot = $env:VELOS_ROOT
if (-not $velosRoot) {
    $velosRoot = (Get-Location).Path
}

# 로그 디렉토리 경로 설정
$logDir = Join-Path $velosRoot "data\logs"

# 로그 디렉토리 존재 확인 및 생성
if (!(Test-Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "로그 디렉토리가 생성되었습니다: $logDir" -ForegroundColor Green
    }
    catch {
        Write-Error "로그 디렉토리 생성 실패: $($_.Exception.Message)"
        exit 1
    }
}

# 타임스탬프 생성
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "git_cleanup_runner_$ts.log"

# 컬러 출력 도우미
function _ok($msg){ Write-Host $msg -ForegroundColor Green }
function _info($msg){ Write-Host $msg -ForegroundColor Cyan }
function _warn($msg){ Write-Host $msg -ForegroundColor Yellow }
function _err($msg){ Write-Host $msg -ForegroundColor Red }

function _log($msg){
    $msg | Out-File -FilePath $logFile -Append -Encoding UTF8
}

# 도움말 표시
if ($Help) {
    Write-Host @"
VELOS Git 저장소 정리 실행 도우미

사용법:
    .\scripts\velos_git_cleanup_runner.ps1 [옵션]

옵션:
    -CommitMessage <메시지>    커밋 메시지 지정
    -DryRun                   실제 변경 없이 시뮬레이션만 실행
    -Force                    확인 없이 강제 실행
    -Help                     이 도움말 표시

실행 예시:
    # 기본 실행 (확인 단계 포함)
    .\scripts\velos_git_cleanup_runner.ps1

    # Dry-Run 모드 (실제 변경 없음)
    .\scripts\velos_git_cleanup_runner.ps1 -DryRun

    # 커스텀 커밋 메시지
    .\scripts\velos_git_cleanup_runner.ps1 -CommitMessage "feat: VELOS 정리 완료"

    # 강제 실행 (확인 없음)
    .\scripts\velos_git_cleanup_runner.ps1 -Force

PowerShell 직접 실행:
    # 워크스페이스 루트에서:
    pwsh -ExecutionPolicy Bypass -File .\scripts\velos_git_cleanup.ps1

    # 메시지 지정
    pwsh -ExecutionPolicy Bypass -File .\scripts\velos_git_cleanup.ps1 -CommitMessage "chore: cleanup + hooks"

    # 사전 점검만(파일은 안 만지고 무엇을 할지 로그/출력만)
    pwsh -ExecutionPolicy Bypass -File .\scripts\velos_git_cleanup.ps1 -DryRun
"@ -ForegroundColor White
    exit 0
}

Write-Host "VELOS Git 저장소 정리 실행 도우미 시작..." -ForegroundColor Cyan
_log "VELOS Git 저장소 정리 실행 도우미 시작: $(Get-Date)"

# 사전 점검
Write-Host "=== 사전 점검 ===" -ForegroundColor Yellow

# 1. Git 저장소 확인
if (-not (Test-Path ".git")) {
    _err "현재 디렉토리가 Git 저장소가 아닙니다."
    _log "오류: Git 저장소가 아님"
    exit 1
}
_ok "✓ Git 저장소 확인됨"

# 2. PowerShell 실행 정책 확인
try {
    $executionPolicy = Get-ExecutionPolicy
    _info "현재 실행 정책: $executionPolicy"
    _log "실행 정책: $executionPolicy"

    if ($executionPolicy -eq "Restricted") {
        _warn "실행 정책이 Restricted입니다. Bypass 모드로 실행됩니다."
    }
} catch {
    _warn "실행 정책 확인 실패: $($_.Exception.Message)"
}

# 3. 스크립트 파일 존재 확인
$scriptPath = Join-Path $velosRoot "scripts\velos_git_cleanup.ps1"
if (-not (Test-Path $scriptPath)) {
    _err "VELOS Git 정리 스크립트를 찾을 수 없습니다: $scriptPath"
    _log "오류: 스크립트 파일 없음 - $scriptPath"
    exit 1
}
_ok "✓ 스크립트 파일 확인됨: $scriptPath"

# 4. 현재 Git 상태 확인
try {
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        _warn "현재 Git 상태 (변경된 파일들):"
        $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        _log "Git 상태: 변경된 파일 있음"
    } else {
        _ok "✓ Git 작업트리가 깨끗합니다."
        _log "Git 상태: 깨끗함"
    }
} catch {
    _warn "Git 상태 확인 실패: $($_.Exception.Message)"
}

# 5. 환경 변수 설정
$env:VELOS_ROOT = $velosRoot
_ok "✓ 환경 변수 설정: VELOS_ROOT = $velosRoot"

# 실행 확인 (Force가 아닌 경우)
if (-not $Force -and -not $DryRun) {
    Write-Host "`n=== 실행 확인 ===" -ForegroundColor Yellow
    Write-Host "다음 작업들이 수행됩니다:" -ForegroundColor White
    Write-Host "  1. 변동성 산출물 VCS 분리 (.gitignore 업데이트)" -ForegroundColor Gray
    Write-Host "  2. pre-commit 훅 설정" -ForegroundColor Gray
    Write-Host "  3. 라인엔딩 정규화" -ForegroundColor Gray
    Write-Host "  4. pre-commit 훅 실행" -ForegroundColor Gray
    Write-Host "  5. 작업트리 정리" -ForegroundColor Gray
    Write-Host "  6. 안전 커밋" -ForegroundColor Gray
    Write-Host "`n커밋 메시지: $CommitMessage" -ForegroundColor Cyan

    $confirm = Read-Host "`n계속하시겠습니까? (Y/N)"
    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        _warn "사용자에 의해 취소되었습니다."
        _log "사용자 취소"
        exit 0
    }
}

# 실행 명령어 구성
$execArgs = @()
if ($DryRun) { $execArgs += "-DryRun" }
if ($CommitMessage -ne "chore: pre-commit excludes + normalize EOL + ignore volatile outputs") {
    $execArgs += "-CommitMessage", "`"$CommitMessage`""
}

$execCommand = "pwsh -ExecutionPolicy Bypass -File `"$scriptPath`""
if ($execArgs.Count -gt 0) {
    $execCommand += " " + ($execArgs -join " ")
}

# 실행
Write-Host "`n=== VELOS Git 정리 스크립트 실행 ===" -ForegroundColor Magenta
_info "실행 명령어: $execCommand"
_log "실행 명령어: $execCommand"

try {
    if ($DryRun) {
        _warn "[DRY-RUN] 실제 실행을 시뮬레이션합니다."
        _log "[DRY-RUN] 시뮬레이션 모드"
    }

    # PowerShell 실행
    $result = Invoke-Expression $execCommand

    _ok "VELOS Git 저장소 정리가 성공적으로 완료되었습니다."
    _log "실행 완료: 성공"

    # 결과 요약
    Write-Host "`n=== 실행 결과 요약 ===" -ForegroundColor Green
    Write-Host "실행 시간: $(Get-Date)" -ForegroundColor White
    Write-Host "로그 파일: $logFile" -ForegroundColor White
    if ($DryRun) {
        Write-Host "모드: Dry-Run (실제 변경 없음)" -ForegroundColor Yellow
    }

} catch {
    _err "VELOS Git 정리 실행 중 오류 발생: $($_.Exception.Message)"
    _log "실행 오류: $($_.Exception.Message)"
    exit 1
}

Write-Host "`nVELOS Git 저장소 정리 실행 도우미가 완료되었습니다." -ForegroundColor Green
