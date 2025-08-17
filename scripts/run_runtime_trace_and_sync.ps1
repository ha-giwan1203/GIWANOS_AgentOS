# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$SETT = $env:VELOS_SETTINGS; if (-not $SETT) { $SETT = Join-Path $ROOT "configs\settings.yaml" }

Write-Host "[VELOS] 런타임 트레이스 + 매니페스트 동기화 시작"
Write-Host "[env] ROOT=$ROOT"
Write-Host "[env] SETTINGS=$SETT"

# 1) 구문 검사
Write-Host "[VELOS] 1단계: Python 구문 검사"
try {
    python -m py_compile (Join-Path $ROOT "tools\analysis\runtime_trace_runner.py")
    python -m py_compile (Join-Path $ROOT "tools\analysis\auto_manifest_sync.py")
    Write-Host "[VELOS] 구문 검사 통과"
} catch {
    Write-Host "[VELOS] 구문 검사 실패: $_"
    exit 1
}

# 2) 트레이스 실행(안전 시나리오: warmload + selftests)
Write-Host "[VELOS] 2단계: 런타임 트레이스 실행"
try {
    $result = python (Join-Path $ROOT "tools\analysis\runtime_trace_runner.py") --mode warmload 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 워밀로드 트레이스 완료"
    } else {
        Write-Host "[VELOS] 워밀로드 트레이스 실패: $result"
    }
} catch {
    Write-Host "[VELOS] 워밀로드 트레이스 오류: $_"
}

try {
    $result = python (Join-Path $ROOT "tools\analysis\runtime_trace_runner.py") --mode selftests 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 세션 스토어 selftest 트레이스 완료"
    } else {
        Write-Host "[VELOS] 세션 스토어 selftest 트레이스 실패: $result"
    }
} catch {
    Write-Host "[VELOS] 세션 스토어 selftest 트레이스 오류: $_"
}

# 필요하면 모듈/스크립트 지정도 가능:
# python tools\analysis\runtime_trace_runner.py --mode module --module interface.velos_dashboard
# python tools\analysis\runtime_trace_runner.py --mode script --script scripts\run_giwanos_master_loop.py

# 3) 매니페스트 자동 동기화
Write-Host "[VELOS] 3단계: 매니페스트 자동 동기화"
try {
    $result = python (Join-Path $ROOT "tools\analysis\auto_manifest_sync.py") 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 매니페스트 동기화 완료"
        Write-Host $result
    } else {
        Write-Host "[VELOS] 매니페스트 동기화 실패: $result"
    }
} catch {
    Write-Host "[VELOS] 매니페스트 동기화 오류: $_"
}

# 4) 결과 안내
Write-Host "[VELOS] 4단계: 결과 확인"
Write-Host "[OK] Trace + Manifest Sync 완료"
Write-Host "Trace logs : $ROOT\data\logs\runtime_trace\trace_*.jsonl"
Write-Host "Manifest   : $ROOT\configs\feature_manifest.yaml"
Write-Host "Report(JSON): $ROOT\data\reports\manifest_sync_report.json"
Write-Host "Report(MD) : $ROOT\data\reports\manifest_sync_report.md"

# 결과 파일 확인
$traceLogs = Join-Path $ROOT "data\logs\runtime_trace"
$manifestFile = Join-Path $ROOT "configs\feature_manifest.yaml"
$syncReport = Join-Path $ROOT "data\reports\manifest_sync_report.json"

Write-Host "[VELOS] 결과 파일 상태:"
if(Test-Path $traceLogs) {
    $traceCount = (Get-ChildItem $traceLogs -Filter "trace_*.jsonl").Count
    Write-Host "  트레이스 로그: $traceCount개 파일"
} else {
    Write-Host "  트레이스 로그: 없음"
}

if(Test-Path $manifestFile) {
    Write-Host "  Manifest: 존재함"
} else {
    Write-Host "  Manifest: 없음"
}

if(Test-Path $syncReport) {
    Write-Host "  동기화 리포트: 존재함"
} else {
    Write-Host "  동기화 리포트: 없음"
}

Write-Host "[VELOS] 런타임 트레이스 + 매니페스트 동기화 완료"
