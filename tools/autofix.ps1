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
