# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Memory Cleaner Runner
$ErrorActionPreference="Stop"
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT="C:\giwanos" }
Write-Host "[VELOS] Memory Cleaner Runner 시작 - $ROOT"

# 1단계: 구문 검사
Write-Host "[STEP] 1단계: Python 구문 검사"
try {
    python -m py_compile (Join-Path $ROOT "modules\automation\memory_cleaner.py")
    Write-Host "[OK] 구문 검사 통과"
} catch {
    Write-Host "[ERR] 구문 검사 실패: $_"
    exit 1
}

# 2단계: 드라이런(로그만)
Write-Host "[STEP] 2단계: Dry-run 실행"
try {
    $result = python (Join-Path $ROOT "modules\automation\memory_cleaner.py") --dry-run
    Write-Host $result
    if($LASTEXITCODE -ne 0) {
        Write-Host "[ERR] Dry-run 실패"
        exit 1
    }
    Write-Host "[OK] Dry-run 완료"
} catch {
    Write-Host "[ERR] Dry-run 실행 중 오류: $_"
    exit 1
}

# 3단계: 실제 실행
Write-Host "[STEP] 3단계: 실제 메모리 클리닝 실행"
try {
    $result = python (Join-Path $ROOT "modules\automation\memory_cleaner.py") --run-clean
    Write-Host $result
    if($LASTEXITCODE -ne 0) {
        Write-Host "[ERR] 메모리 클리닝 실패"
        exit 1
    }
    Write-Host "[OK] 메모리 클리닝 완료"
} catch {
    Write-Host "[ERR] 메모리 클리닝 실행 중 오류: $_"
    exit 1
}

# 4단계: 결과 확인
Write-Host "[STEP] 4단계: 결과 파일 확인"
try {
    $cleaned_file = Join-Path $ROOT "data\memory\learning_memory_cleaned.jsonl"
    $report_file = Join-Path $ROOT "data\reports\memory_clean_report.json"

    if(Test-Path $cleaned_file) {
        Get-Item $cleaned_file | Format-List Name,Length,LastWriteTime
    } else {
        Write-Host "[WARN] 클리닝된 메모리 파일이 없습니다"
    }

    if(Test-Path $report_file) {
        Get-Item $report_file | Format-List Name,Length,LastWriteTime
    } else {
        Write-Host "[WARN] 메모리 클리닝 리포트가 없습니다"
    }

    Write-Host "[OK] 결과 확인 완료"
} catch {
    Write-Host "[ERR] 결과 확인 중 오류: $_"
    exit 1
}

Write-Host "[DONE] VELOS Memory Cleaner Runner 완료!"
