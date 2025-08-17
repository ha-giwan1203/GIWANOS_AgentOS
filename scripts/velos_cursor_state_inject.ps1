# === VELOS 운영 철학 선언문 ===
# 파일명/경로 불변 · 거짓 코드 금지 · 자가 검증 필수 · 결과는 로그로 증빙

$ErrorActionPreference = "Stop"
$ROOT = "C:\giwanos"
$statePath = Join-Path $ROOT "data\memory\runtime_state.json"

# 1) runtime_state.json 읽어 커서 상태 주입
function Get-Json($path) {
    if (-not (Test-Path $path)) { return $null }
    try {
        return Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json
    }
    catch { return $null }
}

$state = Get-Json $statePath
$cursorFlag = $false
if ($state -and $state.cursor_in_use -ne $null) { $cursorFlag = [bool]$state.cursor_in_use }

# 환경변수 주입(세션 범위)
$env:CURSOR_IN_USE = ($cursorFlag ? "1" : "0")
if ($state -and $state.source) { $env:VELOS_SESSION_SOURCE = [string]$state.source }

# 2) 커서 프로세스 감지로 보정(환경 변수 없거나 false인데 실제 커서면 true로 승격)
try {
    $p = Get-Process -ErrorAction SilentlyContinue | ? { $_.ProcessName -match "cursor" }
    if ($p -and $env:CURSOR_IN_USE -ne "1") { $env:CURSOR_IN_USE = "1" }
}
catch {}

# 3) 로그 힌트(선택): system_health.json에 부트 마커 남기는 쪽은 파이썬에서 처리
Write-Host "[VELOS] CURSOR_IN_USE=$($env:CURSOR_IN_USE) VELOS_SESSION_SOURCE=$($env:VELOS_SESSION_SOURCE)"

# 4) 성공 상태 반환 (스크립트 호출자용)
if ($env:CURSOR_IN_USE -eq "1") {
    Write-Host "[VELOS] ✅ Cursor 상태 주입 완료: 사용 중"
    exit 0
}
else {
    Write-Host "[VELOS] ✅ Cursor 상태 주입 완료: 사용 안함"
    exit 0
}
