# === VELOS 선언문 자동 삽입기 (파일명 변경 금지) ===
# 사용: 관리자 PowerShell에서
#   pwsh -File C:\giwanos\scripts\stamp_veilos_philosophy.ps1
# 옵션:
#   -WhatIf  : 실제 쓰기 없이 미리보기
#   -Verbose : 처리 파일 로그 상세 출력
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Root = "C:\giwanos",
    [string[]]$IncludeExt = @("*.py", "*.ps1")
)

$ErrorActionPreference = "Stop"
$headerText = @'
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
'@

$markerBegin = "# VELOS 운영 철학 선언문"
$excludes = @(
    "\\.git($|\\)",
    "\\.venv_link($|\\)",
    "\\.venv($|\\)",
    "site-packages",
    "node_modules",
    "\\.ipynb_checkpoints"
) | ForEach-Object { [regex]::new($_, 'IgnoreCase') }

function Should-Exclude($path) {
    foreach ($rx in $excludes) { if ($rx.IsMatch($path)) { return $true } }
    return $false
}

$targets = @()
foreach ($pat in $IncludeExt) {
    $targets += Get-ChildItem -LiteralPath $Root -Recurse -File -Include $pat -ErrorAction SilentlyContinue
}
$targets = $targets | Where-Object { -not (Should-Exclude $_.FullName) }

Write-Verbose ("Found {0} candidate files" -f $targets.Count)

foreach ($f in $targets) {
    try {
        $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
        if ($content -match [regex]::Escape($markerBegin)) {
            Write-Verbose "SKIP (already stamped): $($f.FullName)"
            continue
        }

        $newContent = $headerText + "`r`n" + $content
        if ($PSCmdlet.ShouldProcess($f.FullName, "prepend VELOS header")) {
            $tmp = "$($f.FullName).tmp"
            $newContent | Set-Content -LiteralPath $tmp -Encoding UTF8
            Move-Item -LiteralPath $tmp -Destination $f.FullName -Force
            Write-Verbose "STAMPED: $($f.FullName)"
        }
    }
    catch {
        Write-Warning "FAIL: $($f.FullName) -> $($_.Exception.Message)"
    }
}

Write-Host "Done. Use -Verbose to see stamped files."
