# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

param([switch]$Verbose)

$ErrorActionPreference = 'Stop'

# 환경변수 설정
$env:VELOS_ROOT = if($env:VELOS_ROOT) { $env:VELOS_ROOT } else { 'C:\giwanos' }
$env:VELOS_SETTINGS = if($env:VELOS_SETTINGS) { $env:VELOS_SETTINGS } else { 'C:\giwanos\configs\settings.yaml' }

Write-Host "[VELOS] 파일 사용성 감사 시작"
Write-Host "[VELOS] ROOT: $env:VELOS_ROOT"
Write-Host "[VELOS] SETTINGS: $env:VELOS_SETTINGS"

# Python 스크립트 실행
try {
    $result = python tools/analysis/file_usage_audit.py 2>&1
    if($LASTEXITCODE -eq 0) {
        Write-Host "[VELOS] 파일 사용성 감사 완료"
        Write-Host $result
    } else {
        Write-Host "[VELOS] 파일 사용성 감사 실패: $result"
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "[VELOS] 오류: $_"
    exit 1
}

# 리포트 파일 확인
$reportJson = Join-Path $env:VELOS_ROOT "data\reports\file_usage_report.json"
$reportMd = Join-Path $env:VELOS_ROOT "data\reports\file_usage_report.md"

if(Test-Path $reportJson) {
    Write-Host "[VELOS] JSON 리포트 생성됨: $reportJson"
} else {
    Write-Host "[VELOS] 경고: JSON 리포트 파일이 생성되지 않음"
}

if(Test-Path $reportMd) {
    Write-Host "[VELOS] Markdown 리포트 생성됨: $reportMd"
} else {
    Write-Host "[VELOS] 경고: Markdown 리포트 파일이 생성되지 않음"
}

Write-Host "[VELOS] 파일 사용성 감사 완료"
