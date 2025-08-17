# VELOS 운영 철학: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

<# ======================================================================
 VELOS pre-commit 훅 업데이트 스크립트
 - 운영 철학: 환경변수 우선, 하드코딩 금지, 안전/검증 가능한 자동화
 - 기능: pre-commit 훅 자동 업데이트, 버전 관리, 백업 및 복구
 ====================================================================== #>

[CmdletBinding()]
param(
    [string]$Repo = "https://github.com/pre-commit/pre-commit-hooks",
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# ── 0) 환경/경로 설정 (운영 철학: 환경변수 우선) ───────────────────────────────
$Root = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { (Get-Location).Path }
$env:VELOS_ROOT = $Root
$LogDir = Join-Path $Root 'data\logs'
$TimeTag = (Get-Date -Format 'yyyyMMdd_HHmmss')
$LogFile = Join-Path $LogDir "precommit_update_$TimeTag.log"

# 컬러 출력 도우미
function _ok($msg){ Write-Host $msg -ForegroundColor Green }
function _info($msg){ Write-Host $msg -ForegroundColor Cyan }
function _warn($msg){ Write-Host $msg -ForegroundColor Yellow }
function _err($msg){ Write-Host $msg -ForegroundColor Red }

function _log($msg){
    $msg | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

function Step($n,$title){
    $h = "=== $n) $title ==="
    Write-Host $h -ForegroundColor Magenta
    _log $h
}

function ExecCommand([string]$cmd, [string]$args = ""){
    if($DryRun){
        _warn "[DRY-RUN] $cmd $args"
        _log "[DRY-RUN] $cmd $args"
        return
    }
    _info "$cmd $args"
    _log "$cmd $args"

    try {
        if ($IsWindows) {
            & cmd.exe /c "$cmd $args" | Tee-Object -FilePath $LogFile -Append
        } else {
            & bash -lc "$cmd $args" | Tee-Object -FilePath $LogFile -Append
        }
    } catch {
        _err "명령어 실행 실패: $($_.Exception.Message)"
        _log "명령어 실행 실패: $($_.Exception.Message)"
        throw
    }
}

# ── 자가 검증: 로그 디렉토리 보장 ───────────────────────────────────────────────
Write-Host "VELOS pre-commit 훅 업데이트 시작..." -ForegroundColor White
Step "0" "현재 작업 디렉토리 확인"
Write-Host "현재 디렉토리: $Root" -ForegroundColor White
if(!(Test-Path $LogDir)){ New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
"Started at $(Get-Date)" | Out-File -FilePath $LogFile -Encoding UTF8

# 도움말 표시
if ($Help) {
    Write-Host @"
VELOS pre-commit 훅 업데이트 스크립트

사용법:
    .\scripts\velos_precommit_update.ps1 [옵션]

옵션:
    -Repo <URL>              업데이트할 저장소 URL (기본값: pre-commit-hooks)
    -DryRun                  실제 변경 없이 시뮬레이션만 실행
    -Force                   확인 없이 강제 실행
    -Help                    이 도움말 표시

실행 예시:
    # 기본 업데이트 (pre-commit-hooks)
    .\scripts\velos_precommit_update.ps1

    # 특정 저장소 업데이트
    .\scripts\velos_precommit_update.ps1 -Repo "https://github.com/pre-commit/pre-commit-hooks"

    # Dry-Run 모드
    .\scripts\velos_precommit_update.ps1 -DryRun

    # 강제 실행
    .\scripts\velos_precommit_update.ps1 -Force

PowerShell 직접 실행:
    pre-commit autoupdate --repo https://github.com/pre-commit/pre-commit-hooks
"@ -ForegroundColor White
    exit 0
}

# ── 1) 사전 점검 ───────────────────────────────────────────────────────────────
Step "1" "사전 점검"

# 1.1 Git 저장소 확인
if (-not (Test-Path ".git")) {
    _err "현재 디렉토리가 Git 저장소가 아닙니다."
    _log "오류: Git 저장소가 아님"
    exit 1
}
_ok "✓ Git 저장소 확인됨"

# 1.2 pre-commit 설정 파일 확인
$precommitConfig = Join-Path $Root ".pre-commit-config.yaml"
if (-not (Test-Path $precommitConfig)) {
    _err "pre-commit 설정 파일을 찾을 수 없습니다: $precommitConfig"
    _log "오류: pre-commit 설정 파일 없음"
    exit 1
}
_ok "✓ pre-commit 설정 파일 확인됨"

# 1.3 pre-commit 설치 확인
try {
    $precommitVersion = pre-commit --version
    _ok "✓ pre-commit 설치 확인됨: $precommitVersion"
    _log "pre-commit 버전: $precommitVersion"
} catch {
    _err "pre-commit이 설치되지 않았습니다. 'pip install pre-commit'으로 설치하세요."
    _log "오류: pre-commit 미설치"
    exit 1
}

# ── 2) 현재 설정 백업 ─────────────────────────────────────────────────────────
Step "2" "현재 설정 백업"

$backupFile = Join-Path $Root ".pre-commit-config.yaml.backup.$TimeTag"
try {
    Copy-Item $precommitConfig $backupFile
    _ok "✓ 설정 파일 백업 완료: $backupFile"
    _log "백업 파일: $backupFile"
} catch {
    _err "백업 생성 실패: $($_.Exception.Message)"
    _log "백업 실패: $($_.Exception.Message)"
    exit 1
}

# ── 3) 현재 버전 정보 확인 ───────────────────────────────────────────────────
Step "3" "현재 버전 정보 확인"

try {
    $currentConfig = Get-Content $precommitConfig -Raw
    _info "현재 pre-commit 설정 내용:"
    _log "현재 설정 내용:"
    $currentConfig | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
        _log "  $_"
    }
} catch {
    _warn "현재 설정 읽기 실패: $($_.Exception.Message)"
}

# ── 4) pre-commit 훅 업데이트 ────────────────────────────────────────────────
Step "4" "pre-commit 훅 업데이트"

# 실행 확인 (Force가 아닌 경우)
if (-not $Force -and -not $DryRun) {
    Write-Host "`n=== 실행 확인 ===" -ForegroundColor Yellow
    Write-Host "다음 작업이 수행됩니다:" -ForegroundColor White
    Write-Host "  - $Repo 저장소 업데이트" -ForegroundColor Gray
    Write-Host "  - pre-commit 훅 최신 버전으로 갱신" -ForegroundColor Gray
    Write-Host "  - 변경사항 자동 커밋" -ForegroundColor Gray

    $confirm = Read-Host "`n계속하시겠습니까? (Y/N)"
    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        _warn "사용자에 의해 취소되었습니다."
        _log "사용자 취소"
        exit 0
    }
}

# pre-commit autoupdate 실행
try {
    ExecCommand "pre-commit" "autoupdate --repo $Repo"
    _ok "✓ pre-commit 훅 업데이트 완료"
} catch {
    _err "pre-commit 훅 업데이트 실패: $($_.Exception.Message)"
    _log "업데이트 실패: $($_.Exception.Message)"

    # 백업에서 복구
    _warn "백업에서 복구를 시도합니다..."
    try {
        Copy-Item $backupFile $precommitConfig -Force
        _ok "✓ 백업에서 복구 완료"
        _log "백업에서 복구 완료"
    } catch {
        _err "백업 복구 실패: $($_.Exception.Message)"
        _log "백업 복구 실패: $($_.Exception.Message)"
        exit 1
    }
    exit 1
}

# ── 5) 업데이트 결과 확인 ───────────────────────────────────────────────────
Step "5" "업데이트 결과 확인"

try {
    $updatedConfig = Get-Content $precommitConfig -Raw
    _info "업데이트된 pre-commit 설정 내용:"
    _log "업데이트된 설정 내용:"
    $updatedConfig | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
        _log "  $_"
    }

    # 변경사항 확인
    $diff = Compare-Object (Get-Content $backupFile) (Get-Content $precommitConfig)
    if ($diff) {
        _ok "✓ 설정 파일에 변경사항이 감지되었습니다."
        _log "변경사항 감지됨"
        $diff | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Yellow
            _log "  $_"
        }
    } else {
        _warn "설정 파일에 변경사항이 없습니다."
        _log "변경사항 없음"
    }
} catch {
    _warn "업데이트 결과 확인 실패: $($_.Exception.Message)"
}

# ── 6) 변경사항 커밋 ─────────────────────────────────────────────────────────
Step "6" "변경사항 커밋"

try {
    # Git 상태 확인
    $gitStatus = git status --porcelain
    if ($gitStatus -match "\.pre-commit-config\.yaml") {
        _info "pre-commit 설정 파일 변경사항을 커밋합니다."

        ExecCommand "git" "add .pre-commit-config.yaml"
        ExecCommand "git" "commit -m `"chore: pre-commit hooks autoupdate - $Repo`""

        _ok "✓ 변경사항 커밋 완료"
        _log "변경사항 커밋 완료"
    } else {
        _info "커밋할 변경사항이 없습니다."
        _log "커밋할 변경사항 없음"
    }
} catch {
    _warn "변경사항 커밋 실패: $($_.Exception.Message)"
    _log "커밋 실패: $($_.Exception.Message)"
}

# ── 자가 검증: 최종 상태 ──────────────────────────────────────────────────────
Write-Host "=== 자가 검증: 최종 상태 확인 ===" -ForegroundColor Magenta
try {
    # pre-commit 훅 테스트
    ExecCommand "pre-commit" "run --all-files"
    _ok "✓ pre-commit 훅 테스트 완료"
} catch {
    _warn "pre-commit 훅 테스트 실패: $($_.Exception.Message)"
    _log "훅 테스트 실패: $($_.Exception.Message)"
}

_ok "pre-commit 훅 업데이트가 성공적으로 완료되었습니다."
Write-Host "VELOS pre-commit 훅 업데이트가 완료되었습니다." -ForegroundColor White
Write-Host "로그 파일: $LogFile" -ForegroundColor White
Write-Host "백업 파일: $backupFile" -ForegroundColor White
