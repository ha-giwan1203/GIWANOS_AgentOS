# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$SETT = $env:VELOS_SETTINGS; if (-not $SETT) { $SETT = Join-Path $ROOT "configs\settings.yaml" }

Write-Host "[VELOS] 런타임 트레이스 스위트 시작"
Write-Host "[env] ROOT=$ROOT"
Write-Host "[env] SETTINGS=$SETT"

# 1단계: 런타임 트레이스 실행
Write-Host "[VELOS] 1단계: 런타임 트레이스 실행"
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

# 2단계: Auto-Manifest Sync
Write-Host "[VELOS] 2단계: Auto-Manifest Sync"
try {
    $result = python (Join-Path $ROOT "tools\analysis\auto_manifest_sync.py") 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] Auto-Manifest Sync 완료"
        Write-Host $result
    } else {
        Write-Host "[VELOS] Auto-Manifest Sync 실패: $result"
    }
} catch {
    Write-Host "[VELOS] Auto-Manifest Sync 오류: $_"
}

# 3단계: 업데이트된 리스크 감사
Write-Host "[VELOS] 3단계: 업데이트된 리스크 감사"
try {
    $result = python (Join-Path $ROOT "tools\analysis\file_usage_risk_audit.py") 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 리스크 감사 완료"
        Write-Host $result
    } else {
        Write-Host "[VELOS] 리스크 감사 실패: $result"
    }
} catch {
    Write-Host "[VELOS] 리스크 감사 오류: $_"
}

# 결과 파일 확인
$traceLogs = Join-Path $ROOT "data\logs\runtime_trace"
$manifestFile = Join-Path $ROOT "configs\feature_manifest.yaml"
$riskReport = Join-Path $ROOT "data\reports\file_usage_risk_report.json"

Write-Host "[VELOS] 결과 파일 확인:"
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

if(Test-Path $riskReport) {
    Write-Host "  리스크 리포트: 존재함"
} else {
    Write-Host "  리스크 리포트: 없음"
}

Write-Host "[VELOS] 런타임 트레이스 스위트 완료"
