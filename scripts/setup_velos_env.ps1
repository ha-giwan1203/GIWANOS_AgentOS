# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

# VELOS 환경 변수 설정
Write-Host "=== VELOS 환경 변수 설정 ===" -ForegroundColor Green

# 기본 환경 변수 설정
$env:VELOS_ROOT = "C:\giwanos"
$env:VELOS_DB = "C:\giwanos\data\velos.db"
$env:VELOS_JSONL_DIR = "C:\giwanos\data\memory"

# 추가 환경 변수 설정
$env:VELOS_RECENT_DAYS = "3"
$env:VELOS_KEYWORD_MAXLEN = "24"
$env:VELOS_FTS_LIMIT = "20"

Write-Host "환경 변수 설정 완료:" -ForegroundColor Yellow
Write-Host "  VELOS_ROOT: $env:VELOS_ROOT" -ForegroundColor Cyan
Write-Host "  VELOS_DB: $env:VELOS_DB" -ForegroundColor Cyan
Write-Host "  VELOS_JSONL_DIR: $env:VELOS_JSONL_DIR" -ForegroundColor Cyan
Write-Host "  VELOS_RECENT_DAYS: $env:VELOS_RECENT_DAYS" -ForegroundColor Cyan
Write-Host "  VELOS_KEYWORD_MAXLEN: $env:VELOS_KEYWORD_MAXLEN" -ForegroundColor Cyan
Write-Host "  VELOS_FTS_LIMIT: $env:VELOS_FTS_LIMIT" -ForegroundColor Cyan

# 디렉토리 존재 확인
Write-Host "`n디렉토리 확인:" -ForegroundColor Yellow
if (Test-Path $env:VELOS_ROOT) {
    Write-Host "  ✅ VELOS_ROOT 존재: $env:VELOS_ROOT" -ForegroundColor Green
} else {
    Write-Host "  ❌ VELOS_ROOT 없음: $env:VELOS_ROOT" -ForegroundColor Red
}

if (Test-Path $env:VELOS_JSONL_DIR) {
    Write-Host "  ✅ VELOS_JSONL_DIR 존재: $env:VELOS_JSONL_DIR" -ForegroundColor Green
} else {
    Write-Host "  ❌ VELOS_JSONL_DIR 없음: $env:VELOS_JSONL_DIR" -ForegroundColor Red
}

# DB 파일 확인
if (Test-Path $env:VELOS_DB) {
    Write-Host "  ✅ VELOS_DB 존재: $env:VELOS_DB" -ForegroundColor Green
    $dbSize = (Get-Item $env:VELOS_DB).Length
    Write-Host "  📊 DB 크기: $([math]::Round($dbSize/1KB, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️ VELOS_DB 없음 (ingest에서 생성됨): $env:VELOS_DB" -ForegroundColor Yellow
}

Write-Host "`n=== 환경 변수 설정 완료 ===" -ForegroundColor Green
