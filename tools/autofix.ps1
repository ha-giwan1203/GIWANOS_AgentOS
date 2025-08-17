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
param([switch]$Once)
$ErrorActionPreference = "Stop"

function Run-Tests {
    Write-Host "[autofix] pytest 실행" -ForegroundColor Cyan
    $out = (& python -m pytest -q 2>&1) | Out-String
    $code = $LASTEXITCODE
    return @{ code = $code; log = $out }
}

function Have-CursorAgent {
    try { Get-Command cursor-agent -ErrorAction Stop | Out-Null; return $true } catch { return $false }
}

function Minimal-Fix([string]$log, [string]$diff) {
    if (-not (Have-CursorAgent)) {
        Write-Host "[autofix] cursor-agent 없음. 자동수정 스킵" -ForegroundColor DarkYellow
        return
    }
    $prompt = @"
테스트 실패를 최소 수정으로 고쳐라.
규칙: VELOS 경로는 환경변수 기반(절대경로 금지), 변경은 필요한 부분만.
테스트 로그:
$log

Diff(기준):
$diff
"@
    cursor-agent -p $prompt --print | Out-Null
}

# 허용/차단 패턴
$ALLOW = @('*.py','*.ps1','*.md','*.json','*.yaml','*.yml')
$BLOCK = @('configs/.env','data/backups/*','data/reports/_dispatch/_failed/*','data/reports/_dispatch_processed/*')

function Match-Any($path, $patterns) {
    foreach ($p in $patterns) {
        if ([System.Management.Automation.WildcardPattern]::new($p,[System.Management.Automation.WildcardOptions]::IgnoreCase).IsMatch($path)) { return $true }
    }
    return $false
}

# porcelain 파싱: XY status + 경로 (리네임은 old -> new)
function Get-Changes {
    $lines = git status --porcelain | ForEach-Object { $_.TrimEnd() } | Where-Object { $_ }
    $out = @()
    foreach ($l in $lines) {
        if ($l -match '^(?<st>.{2})\s+(?<rest>.+)$') {
            $st = $Matches.st
            $rest = $Matches.rest
            $old = $null; $new = $rest
            if ($rest -like '* -> *') {
                $parts = $rest -split '\s+->\s+'
                $old = $parts[0]; $new = $parts[1]
            }
            $obj = [pscustomobject]@{ Status=$st; Old=$old; Path=$new }
            $out += $obj
        }
    }
    return $out
}

function Stage-Allowed {
    $changes = Get-Changes
    if (-not $changes -or $changes.Count -eq 0) { return $false }

    $stagedSomething = $false
    $blocked = @()

    foreach ($c in $changes) {
        $p = $c.Path
        $o = $c.Old

        # 차단 경로 제외
        if (Match-Any $p $BLOCK -or ($o -and (Match-Any $o $BLOCK))) {
            $blocked += $p
            continue
        }
        # 허용 확장자만 처리
        if (-not (Match-Any $p $ALLOW) -and -not ($o -and (Match-Any $o $ALLOW))) { continue }

        $X = $c.Status.Substring(0,1)
        $Y = $c.Status.Substring(1,1)

        # 삭제 처리: 파일이 물리적으로 없으면 rm, 있으면 add
        if ($X -eq 'D' -or $Y -eq 'D') {
            git rm --quiet --ignore-unmatch -- $p 2>$null
            if ($o) { git rm --quiet --ignore-unmatch -- $o 2>$null }
            $stagedSomething = $true
            continue
        }

        # 리네임/변경: 구경로 제거 후 신경로 추가
        if ($X -eq 'R' -or $Y -eq 'R' -or $o) {
            if ($o) { git rm --quiet --ignore-unmatch -- $o 2>$null }
            if (Test-Path $p) { git add -- $p | Out-Null }
            $stagedSomething = $true
            continue
        }

        # 그 외 변경: 존재하면 add
        if (Test-Path $p) {
            git add -- $p | Out-Null
            $stagedSomething = $true
        }
    }

    if ($blocked.Count -gt 0) {
        Write-Host "🚫 Path blocked (secrets/backup):" -ForegroundColor DarkYellow
        $blocked | Sort-Object -Unique | ForEach-Object { Write-Host "  - $_" -ForegroundColor DarkYellow }
    }
    return $stagedSomething
}

function Commit-If-Allowed {
    if (Stage-Allowed) {
        try {
            git -c user.email=ci@local -c user.name=ci commit -m "autofix: minimal patch via Cursor agent" | Out-Null
            Write-Host "[autofix] 변경 커밋" -ForegroundColor Green
        } catch {
            Write-Host "[autofix] 커밋 실패: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "[autofix] 커밋할 유효 변경 없음" -ForegroundColor DarkGray
    }
}

function Run-Once {
    $t = Run-Tests
    if ($t.code -ne 0) {
        $diff = (git diff --unified=0) | Out-String
        Minimal-Fix -log $t.log -diff $diff
        Commit-If-Allowed
    } else {
        Write-Host "[autofix] 테스트 통과" -ForegroundColor Green
    }
}

if ($Once) { Run-Once; exit 0 }

Write-Host "[autofix] 파일 변경 감시 시작 (3초 간격)" -ForegroundColor Cyan
while ($true) {
    Start-Sleep 3
    $dirty = (git status --porcelain) | Out-String
    if ($dirty.Trim().Length -gt 0) { Run-Once }
}
