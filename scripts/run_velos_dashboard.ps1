# [ACTIVE] VELOS 대시보드 실행 시스템 - REPORT_KEY 대시보드 실행 스크립트
# VELOS REPORT_KEY 대시보드 실행 스크립트
# 종합적인 REPORT_KEY 검색 및 분석 도구

$ErrorActionPreference = "Stop"

Write-Host "🔍 VELOS REPORT_KEY 대시보드 시작" -ForegroundColor Green
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
$dashboardScript = "C:\giwanos\scripts\velos_dashboard.py"
if (-not (Test-Path $dashboardScript)) {
    Write-Host "❌ 대시보드 스크립트를 찾을 수 없습니다" -ForegroundColor Red
    Write-Host "   경로: $dashboardScript" -ForegroundColor Yellow
    exit 1
}

# 환경변수 로드
Write-Host "🔧 환경변수 로드 중..." -ForegroundColor Cyan
try {
    & $pythonPath -c "from env_loader import load_env; load_env(); print('✅ 환경변수 로드 완료')"
} catch {
    Write-Host "⚠️  환경변수 로드 실패 (선택사항)" -ForegroundColor Yellow
}

Write-Host "🚀 VELOS 대시보드 시작 중..." -ForegroundColor Cyan
Write-Host "   브라우저에서 http://localhost:8501 을 열어주세요" -ForegroundColor Yellow
Write-Host "   Ctrl+C로 대시보드를 종료할 수 있습니다" -ForegroundColor Gray
Write-Host ""

# 대시보드 기능 안내
Write-Host "📋 대시보드 기능:" -ForegroundColor Cyan
Write-Host "   📄 로컬 파일 검색: 로그, 보고서, 회고, 메모리, 세션, 스냅샷" -ForegroundColor Gray
Write-Host "   🗃️ Notion DB 검색: REPORT_KEY로 데이터베이스 검색" -ForegroundColor Gray
Write-Host "   💬 Slack 메시지 검색: 채널 메시지에서 REPORT_KEY 검색" -ForegroundColor Gray
Write-Host "   🧾 로그 미리보기: 주요 로그 파일의 최근 내용" -ForegroundColor Gray
Write-Host "   📊 검색 결과 요약: 통계 및 메트릭 표시" -ForegroundColor Gray
Write-Host ""

# Streamlit 대시보드 실행
try {
    & $pythonPath -m streamlit run $dashboardScript --server.port 8501 --server.address localhost
} catch {
    Write-Host "❌ VELOS 대시보드 실행 실패" -ForegroundColor Red
    Write-Host "   오류: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
}



