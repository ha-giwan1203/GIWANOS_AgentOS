# [ACTIVE] VELOS 검색 앱 실행 시스템 - REPORT_KEY 검색 Streamlit 앱 실행 스크립트
# VELOS REPORT_KEY 검색 Streamlit 앱 실행 스크립트
# Streamlit 기반 웹 인터페이스로 REPORT_KEY 검색

$ErrorActionPreference = "Stop"

Write-Host "🔍 VELOS Report Key Search 앱 시작" -ForegroundColor Green
Write-Host "=" * 50

# Python 가상환경 확인
$pythonPath = "C:\Users\User\venvs\velos\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Host "❌ Python 가상환경을 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "   경로: $pythonPath" -ForegroundColor Yellow
    exit 1
}

# Streamlit 설치 확인
Write-Host "📦 Streamlit 설치 확인 중..." -ForegroundColor Cyan
try {
    & $pythonPath -c "import streamlit; print('✅ Streamlit 설치됨')"
} catch {
    Write-Host "❌ Streamlit이 설치되지 않았습니다" -ForegroundColor Red
    Write-Host "   설치 중..." -ForegroundColor Yellow

    try {
        & $pythonPath -m pip install streamlit
        Write-Host "✅ Streamlit 설치 완료" -ForegroundColor Green
    } catch {
        Write-Host "❌ Streamlit 설치 실패" -ForegroundColor Red
        exit 1
    }
}

# 앱 스크립트 확인
$appScript = "C:\giwanos\scripts\velos_report_search.py"
if (-not (Test-Path $appScript)) {
    Write-Host "❌ 앱 스크립트를 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "   경로: $appScript" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Streamlit 앱 시작 중..." -ForegroundColor Cyan
Write-Host "   브라우저에서 http://localhost:8501 을 열어주세요" -ForegroundColor Yellow
Write-Host "   Ctrl+C로 앱을 종료할 수 있습니다" -ForegroundColor Gray
Write-Host ""

# Streamlit 앱 실행
try {
    & $pythonPath -m streamlit run $appScript --server.port 8501 --server.address localhost
} catch {
    Write-Host "❌ Streamlit 앱 실행 실패" -ForegroundColor Red
    Write-Host "   오류: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
}



