# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$SETT = $env:VELOS_SETTINGS; if (-not $SETT) { $SETT = Join-Path $ROOT "configs\settings.yaml" }
$env:VELOS_DELETION_GUARD = "paranoid"  # 기본: 극보수. 삭제 금지 모드.

Write-Host "[VELOS] 파일 사용성 리스크 감사 시작"
Write-Host "[env] ROOT=$ROOT"
Write-Host "[env] SETTINGS=$SETT"
Write-Host "[env] GUARD=$env:VELOS_DELETION_GUARD"

# Python 스크립트 문법 검증
try {
    python -m py_compile (Join-Path $ROOT "tools\analysis\file_usage_risk_audit.py")
    Write-Host "[VELOS] Python 문법 검증 통과"
} catch {
    Write-Host "[VELOS] Python 문법 오류: $_"
    exit 1
}

# 리스크 감사 실행
try {
    $result = python (Join-Path $ROOT "tools\analysis\file_usage_risk_audit.py") 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 리스크 감사 완료"
        Write-Host $result
    } else {
        Write-Host "[VELOS] 리스크 감사 실패: $result"
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "[VELOS] 오류: $_"
    exit 1
}

# 리포트 파일 확인
$J = Join-Path $ROOT "data\reports\file_usage_risk_report.json"
$M = Join-Path $ROOT "data\reports\file_usage_risk_report.md"

if (Test-Path $J -PathType Leaf -and Test-Path $M -PathType Leaf) {
    Write-Host "[VELOS] 보고서 생성 성공"
    Write-Host "JSON: $J"
    Write-Host "MD  : $M"

    # 요약 정보 출력
    try {
        $jsonContent = Get-Content $J -Raw | ConvertFrom-Json
        Write-Host "[VELOS] 분류 결과:"
        Write-Host "  KEEP_STRICT: $($jsonContent.summary.KEEP_STRICT)"
        Write-Host "  KEEP: $($jsonContent.summary.KEEP)"
        Write-Host "  REVIEW: $($jsonContent.summary.REVIEW)"
        Write-Host "  QUARANTINE_CANDIDATE: $($jsonContent.summary.QUARANTINE_CANDIDATE)"
    } catch {
        Write-Host "[VELOS] 요약 정보 읽기 실패: $_"
    }
} else {
    throw "보고서 생성 실패 - 파일이 존재하지 않음"
}

Write-Host "[VELOS] 파일 사용성 리스크 감사 완료"
