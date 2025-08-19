# [ACTIVE] VELOS REPORT_KEY 대시보드 실행 스크립트 (새 버전)
# 간결하고 효율적인 REPORT_KEY 검색 도구

$ErrorActionPreference = "Stop"

Write-Host "🔎 VELOS REPORT_KEY 대시보드 (새 버전) 시작" -ForegroundColor Green
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

# 대시보드 스크립트 확인
$dashboardScript = "C:\giwanos\scripts\reportkey_dashboard.py"
if (-not (Test-Path $dashboardScript)) {
    Write-Host "❌ 대시보드 스크립트를 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "   경로: $dashboardScript" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 VELOS REPORT_KEY 대시보드 시작 중..." -ForegroundColor Cyan
Write-Host "   브라우저에서 http://localhost:8501 을 열어주세요" -ForegroundColor Yellow
Write-Host "   Ctrl+C로 대시보드를 종료할 수 있습니다" -ForegroundColor Gray
Write-Host ""

# 새 대시보드 기능 안내
Write-Host "📋 새 대시보드 특징:" -ForegroundColor Cyan
Write-Host "   🎯 간결하고 효율적인 검색" -ForegroundColor Gray
Write-Host "   📁 파일 유형별 자동 분류" -ForegroundColor Gray
Write-Host "   📄 PDF, Markdown, JSON, 로그 파일 지원" -ForegroundColor Gray
Write-Host "   🔧 환경변수로 검색 경로 확장 가능" -ForegroundColor Gray
Write-Host "   ⚡ 100MB 이상 파일 자동 스킵" -ForegroundColor Gray
Write-Host ""

# Streamlit 대시보드 실행
try {
    & $pythonPath -m streamlit run $dashboardScript --server.port 8501 --server.address localhost
} catch {
    Write-Host "❌ VELOS REPORT_KEY 대시보드 실행 실패" -ForegroundColor Red
    Write-Host "   오류: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
}




