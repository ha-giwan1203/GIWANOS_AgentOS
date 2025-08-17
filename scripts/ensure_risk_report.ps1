# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference="Stop"
$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}
$rep=Join-Path $ROOT "data\reports\file_usage_risk_report.json"

Write-Host "[VELOS] 리스크 리포트 보장 시작 - $ROOT"

function Fresh($p){
    if(!(Test-Path $p)){
        return $false
    }
    return ((Get-Date) - (Get-Item $p).LastWriteTime).TotalDays -lt 7
}

if(-not (Fresh $rep)){
    Write-Host "[INFO] risk report missing/stale → regenerate"

    # 1단계: 런타임 트레이스 + 매니페스트 동기화
    Write-Host "[STEP] 1단계: 런타임 트레이스 + 매니페스트 동기화"
    try {
        powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT\scripts\run_runtime_trace_and_sync.ps1"
        if($LASTEXITCODE -ne 0) {
            throw "Runtime trace failed with exit code $LASTEXITCODE"
        }
        Write-Host "[OK] 런타임 트레이스 + 매니페스트 동기화 완료"
    } catch {
        Write-Host "[ERR] 런타임 트레이스 실패: $_"
        exit 1
    }

    # 2단계: 리스크 감사 실행
    Write-Host "[STEP] 2단계: 리스크 감사 실행"
    try {
        python "$ROOT\tools\analysis\file_usage_risk_audit.py"
        if($LASTEXITCODE -ne 0) {
            throw "Risk audit failed with exit code $LASTEXITCODE"
        }
        Write-Host "[OK] 리스크 감사 완료"
    } catch {
        Write-Host "[ERR] 리스크 감사 실패: $_"
        exit 1
    }
} else {
    Write-Host "[INFO] risk report is fresh"
}

# 검증
Write-Host "[STEP] 3단계: 리포트 검증"
try {
    $j = Get-Content $rep -Raw | ConvertFrom-Json
    if(-not $j.summary){
        throw "risk report invalid - summary missing"
    }

    $orphan = [int]$j.summary.orphan_candidate
    $quarantine = [int]$j.summary.QUARANTINE_CANDIDATE

    Write-Host "[INFO] orphan_candidate: $orphan"
    Write-Host "[INFO] QUARANTINE_CANDIDATE: $quarantine"
    Write-Host "[OK] risk report present & fresh"

} catch {
    Write-Host "[ERR] 리포트 검증 실패: $_"
    exit 1
}

Write-Host "[PASS] 리스크 리포트 보장 완료"
