# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Reflection Risk Tagger Runner
$ErrorActionPreference="Stop"
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT="C:\giwanos" }
Write-Host "[VELOS] Reflection Risk Tagger Runner 시작 - $ROOT"

# 1단계: 구문 검사
Write-Host "[STEP] 1단계: Python 구문 검사"
try {
    python -m py_compile (Join-Path $ROOT "modules\automation\reflection_risk_tagger.py")
    Write-Host "[OK] 구문 검사 통과"
} catch {
    Write-Host "[ERR] 구문 검사 실패: $_"
    exit 1
}

# 2단계: 기본 실행 (메모리만)
Write-Host "[STEP] 2단계: 기본 리스크 태깅 실행"
try {
    $result = python (Join-Path $ROOT "modules\automation\reflection_risk_tagger.py")
    Write-Host $result
    if($LASTEXITCODE -ne 0) {
        Write-Host "[ERR] 리스크 태깅 실패"
        exit 1
    }
    Write-Host "[OK] 기본 리스크 태깅 완료"
} catch {
    Write-Host "[ERR] 리스크 태깅 실행 중 오류: $_"
    exit 1
}

# 3단계: 회고 포함 실행 (선택적)
Write-Host "[STEP] 3단계: 회고 포함 리스크 태깅 실행"
try {
    $result = python (Join-Path $ROOT "modules\automation\reflection_risk_tagger.py") --include-reflections
    Write-Host $result
    if($LASTEXITCODE -ne 0) {
        Write-Host "[ERR] 회고 포함 리스크 태깅 실패"
        exit 1
    }
    Write-Host "[OK] 회고 포함 리스크 태깅 완료"
} catch {
    Write-Host "[ERR] 회고 포함 리스크 태깅 실행 중 오류: $_"
    exit 1
}

# 4단계: 결과 확인
Write-Host "[STEP] 4단계: 결과 파일 확인"
try {
    $json_file = Join-Path $ROOT "data\reports\reflection_risk_report.json"
    $md_file = Join-Path $ROOT "data\reports\reflection_risk_report.md"

    if(Test-Path $json_file) {
        Get-Item $json_file | Format-List Name,Length,LastWriteTime
        $content = Get-Content $json_file -Raw | ConvertFrom-Json
        Write-Host "[INFO] 총 항목: $($content.counts.total), HIGH: $($content.counts.HIGH), MED: $($content.counts.MED), LOW: $($content.counts.LOW)"
    } else {
        Write-Host "[WARN] 리스크 리포트 JSON이 없습니다"
    }

    if(Test-Path $md_file) {
        Get-Item $md_file | Format-List Name,Length,LastWriteTime
    } else {
        Write-Host "[WARN] 리스크 리포트 MD가 없습니다"
    }

    Write-Host "[OK] 결과 확인 완료"
} catch {
    Write-Host "[ERR] 결과 확인 중 오류: $_"
    exit 1
}

Write-Host "[DONE] VELOS Reflection Risk Tagger Runner 완료!"
