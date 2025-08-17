<# ======================================================================
 VELOS Git 저장소 정리 스크립트
 - 운영 철학: 환경변수 우선, 하드코딩 금지, 안전/검증 가능한 자동화
 - 기능: 변동성 산출물 VCS 분리, pre-commit 설정, 라인엔딩 정규화,
         자동수정 훅 루프 차단, 안전 커밋, 자가검증/로깅
 ====================================================================== #>

[CmdletBinding()]
param(
  [string]$CommitMessage = "chore: pre-commit excludes + normalize EOL + ignore volatile outputs",
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# ── 0) 환경/경로 설정 (운영 철학: 환경변수 우선) ───────────────────────────────
$Root = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { (Get-Location).Path }
$env:VELOS_ROOT = $Root
$LogDir = Join-Path $Root 'data\logs'
$TimeTag = (Get-Date -Format 'yyyyMMdd_HHmmss')
$LogFile = Join-Path $LogDir "git_cleanup_$TimeTag.log"

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

function ExecGit {
  param(
    [string]$CmdLine    # 예약변수 피하려고 이름 변경
  )
  if($DryRun){ _warn "[DRY-RUN] git $CmdLine"; _log "[DRY-RUN] git $CmdLine"; return }

  _info "git $CmdLine"
  _log  "git $CmdLine"

  if ($IsWindows) {
    # cmd.exe가 공백/따옴표 포함 인자 파싱을 대신 처리
    & cmd.exe /c "git $CmdLine" | Tee-Object -FilePath $LogFile -Append
  } else {
    # 리눅스/맥일 땐 bash 통해 동일 처리
    & bash -lc "git $CmdLine"   | Tee-Object -FilePath $LogFile -Append
  }
}

# 파일에 특정 라인 보장(중복 방지)
function EnsureLineInFile([string]$path,[string]$line){
  if(!(Test-Path $path)){ New-Item -ItemType File -Path $path -Force | Out-Null }
  $content = Get-Content $path -Raw -ErrorAction SilentlyContinue
  if($content -notmatch [regex]::Escape($line)){
    ($content.TrimEnd() + "`r`n$line`r`n") | Set-Content -Path $path -Encoding UTF8
    _ok  "  + $([System.IO.Path]::GetFileName($path)): '$line' 추가"
    _log "ADD-LINE [$path]: $line"
  } else {
    _info "  = $([System.IO.Path]::GetFileName($path)): 이미 존재"
  }
}

# 파일 내용을 "다르면만" 갱신
function EnsureFileContent([string]$path,[string]$content){
  $new = $content.TrimEnd() + "`r`n"
  $old = (Test-Path $path) ? (Get-Content $path -Raw) : ""
  if($old -ne $new){
    if($DryRun){ _warn "[DRY-RUN] $path 업데이트 예정"; return }
    $dir = Split-Path $path
    if(!(Test-Path $dir)){ New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $path -Value $new -Encoding UTF8
    _ok  "  * $([System.IO.Path]::GetFileName($path)) 갱신"
    _log "WRITE [$path] (updated)"
  } else {
    _info "  = $([System.IO.Path]::GetFileName($path)) 변경 없음"
  }
}

# ── 자가 검증: 로그 디렉토리 보장 ───────────────────────────────────────────────
Write-Host "VELOS Git 저장소 정리 시작..." -ForegroundColor White
Step  "0" "현재 작업 디렉토리 확인"
Write-Host "현재 디렉토리: $Root" -ForegroundColor White
if(!(Test-Path $LogDir)){ New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
"Started at $(Get-Date)" | Out-File -FilePath $LogFile -Encoding UTF8

# Git 리포지터리 유효성
try {
  ExecGit 'rev-parse --is-inside-work-tree' | Out-Null
} catch {
  _err "이 디렉토리는 Git 저장소가 아닙니다."; _log "NOT A GIT REPO"; exit 1
}

# ── 1) 변동성 산출물 VCS 분리  ────────────────────────────────────────────────
Step  "1" "변동성 산출물 VCS 분리"
$gitignore = Join-Path $Root ".gitignore"
EnsureLineInFile $gitignore "# volatile runtime outputs"
EnsureLineInFile $gitignore "/data/logs/"
EnsureLineInFile $gitignore "/data/reports/report_cursor.json"

# 인덱스에서 캐시 제거(이미 추적 중인 경우)
try {
  ExecGit "rm --cached -r data/logs"    # 폴더
} catch { _warn "data/logs 인덱스 제거 스킵: $($_.Exception.Message)" }
try {
  ExecGit "rm --cached data/reports/report_cursor.json" # 단일 파일
} catch { _warn "report_cursor.json 인덱스 제거 스킵: $($_.Exception.Message)" }

# ── 2) pre-commit 훅 설정(데이터/바이너리 제외) ───────────────────────────────
Step  "2" "pre-commit 훅 설정"
$preCommit = @'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
        exclude: ^data/|^velos\.db$|\.zip$|\.pdf$|\.csv$
      - id: trailing-whitespace
        exclude: ^data/|^velos\.db$|\.zip$|\.pdf$|\.csv$
      - id: check-yaml
        exclude: ^data/
  - repo: local
    hooks:
      - id: mypy-minimal
        name: mypy (router only)
        entry: python -m mypy
        language: system
        types_or: [python]
        args: ["--config-file", "mypy.ini"]
        pass_filenames: false   # ← 중요! pre-commit이 파일 목록을 안 넘기게
'@
EnsureFileContent (Join-Path $Root ".pre-commit-config.yaml") $preCommit
_ok ".pre-commit-config.yaml 생성/갱신 완료"

# ── 3) 라인엔딩 정규화(.gitattributes) ───────────────────────────────────────
Step  "3" "라인엔딩 재정규화"
$gitattributes = @'
* text=auto

# Windows 스크립트는 CRLF, 소스/문서/데이터는 LF
*.ps1 eol=crlf
*.bat eol=crlf
*.cmd eol=crlf
*.sh  eol=lf
*.py  eol=lf
*.md  eol=lf
*.json eol=lf
*.yml eol=lf
*.yaml eol=lf

# 바이너리
*.zip binary
*.pdf binary
*.db  binary
*.sqlite binary
'@
EnsureFileContent (Join-Path $Root ".gitattributes") $gitattributes

ExecGit "add .gitattributes"
ExecGit "add --renormalize ."

# ── 4) pre-commit 훅 전체 실행 → 수정 반영 → 스테이징 ─────────────────────────
Step  "4" "pre-commit 훅 실행"
try {
  if(-not $DryRun){ pre-commit run --all-files | Tee-Object -FilePath $LogFile -Append }
  _ok  "pre-commit 훅 실행 완료"
} catch {
  _warn "훅 실행 중 자동수정이 발생했습니다(정상). 변경사항 스테이징으로 이어갑니다."
}
ExecGit "add -A"

# ── 5) 작업트리 정리(훅 자동수정 루프 차단) ───────────────────────────────────
Step  "5" "작업트리 정리"
# 변동성 파일은 워킹트리만 되돌림(추적 제외 + 훅 루프 차단)
foreach($volatile in @("data/logs/system_health.json","data/reports/report_cursor.json")){
  if(Test-Path (Join-Path $Root $volatile)){
    try { ExecGit "restore --worktree $volatile" } catch {}
  }
}
# 상태 점검
$dirty = (git status --porcelain)
if([string]::IsNullOrWhiteSpace($dirty)){
  _ok "작업트리가 깨끗합니다."
}else{
  _warn "남은 변경이 있습니다. 자동 스테이징 시도."
  ExecGit "add -A"
}

# ── 6) 안전 커밋(충돌 최소화: stash -k → commit → pop) ───────────────────────
Step  "6" "안전 커밋"
try {
  if($DryRun){
    _warn "[DRY-RUN] 커밋을 생략합니다."
  } else {
    ExecGit 'stash push -u -k -m "temp-precommit"'
    ExecGit "commit -m `"$CommitMessage`""
    ExecGit "stash pop"  # 충돌나면 사용자가 직접 정리
  }
  _ok "커밋 절차 완료"
} catch {
  _err "커밋 중 오류: $($_.Exception.Message)"
  _log "COMMIT-ERROR: $($_.Exception)"
  throw
}

# ── 자가 검증: 최종 상태 ──────────────────────────────────────────────────────
Write-Host "=== 자가 검증: 최종 상태 확인 ===" -ForegroundColor Magenta
try {
  $last = git log -1 --pretty=format:"%h %ad %s" --date=iso
  _ok  "마지막 커밋: $last"
} catch {
  _warn "커밋 로그 조회 실패: $($_.Exception.Message)"
}

_ok "모든 변경사항이 성공적으로 커밋되었습니다."
Write-Host "VELOS Git 저장소 정리가 완료되었습니다." -ForegroundColor White
Write-Host "로그 파일: $LogFile" -ForegroundColor White
