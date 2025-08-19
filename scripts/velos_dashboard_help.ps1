# [ACTIVE] VELOS 대시보드 도움말 시스템 - REPORT_KEY 대시보드 사용법 안내
# VELOS REPORT_KEY 대시보드 사용법 안내
# 종합적인 REPORT_KEY 검색 및 분석 도구

$ErrorActionPreference = "Stop"

Write-Host "🔍 VELOS REPORT_KEY 대시보드" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📋 대시보드 특징:" -ForegroundColor Cyan
Write-Host "   🎯 REPORT_KEY 하나로 모든 관련 정보 검색" -ForegroundColor Gray
Write-Host "   📊 시각적이고 직관적인 웹 인터페이스" -ForegroundColor Gray
Write-Host "   🔗 로컬 파일, Notion DB, Slack 메시지 통합 검색" -ForegroundColor Gray
Write-Host "   📈 실시간 통계 및 메트릭 제공" -ForegroundColor Gray

Write-Host "`n🚀 실행 방법:" -ForegroundColor Cyan

Write-Host "`n1️⃣ PowerShell 스크립트 실행" -ForegroundColor Yellow
Write-Host "   가장 간단한 방법" -ForegroundColor Gray
Write-Host "   명령어: .\scripts\run_velos_dashboard.ps1" -ForegroundColor White
Write-Host "   브라우저: http://localhost:8501" -ForegroundColor White

Write-Host "`n2️⃣ 직접 Python 실행" -ForegroundColor Yellow
Write-Host "   Streamlit 앱을 직접 실행" -ForegroundColor Gray
Write-Host "   명령어: streamlit run scripts\velos_dashboard.py" -ForegroundColor White

Write-Host "`n3️⃣ Python 모듈 실행" -ForegroundColor Yellow
Write-Host "   Python 모듈로 실행" -ForegroundColor Gray
Write-Host "   명령어: python -m streamlit run scripts\velos_dashboard.py" -ForegroundColor White

Write-Host "`n📂 검색되는 항목들:" -ForegroundColor Cyan
Write-Host "   📄 로컬 파일:" -ForegroundColor Gray
Write-Host "      - 로그: data/logs/*.json, *.log" -ForegroundColor White
Write-Host "      - 보고서: data/reports/**/*" -ForegroundColor White
Write-Host "      - 회고: data/reflections/*.json" -ForegroundColor White
Write-Host "      - 메모리: data/memory/*.json" -ForegroundColor White
Write-Host "      - 세션: data/sessions/*.json" -ForegroundColor White
Write-Host "      - 스냅샷: data/snapshots/**/*" -ForegroundColor White

Write-Host "`n   🗃️ Notion DB:" -ForegroundColor Gray
Write-Host "      - 데이터베이스에서 REPORT_KEY 검색" -ForegroundColor White
Write-Host "      - 페이지 링크 자동 생성" -ForegroundColor White
Write-Host "      - 생성 시간 표시" -ForegroundColor White

Write-Host "`n   💬 Slack 메시지:" -ForegroundColor Gray
Write-Host "      - 채널 메시지에서 REPORT_KEY 검색" -ForegroundColor White
Write-Host "      - 메시지 링크 제공" -ForegroundColor White
Write-Host "      - 전송 시간 표시" -ForegroundColor White

Write-Host "`n   🧾 로그 미리보기:" -ForegroundColor Gray
Write-Host "      - 주요 로그 파일의 최근 내용" -ForegroundColor White
Write-Host "      - Tail 라인 수 조절 가능" -ForegroundColor White
Write-Host "      - 실시간 로그 확인" -ForegroundColor White

Write-Host "`n🔍 검색 예시:" -ForegroundColor Cyan
Write-Host "   REPORT_KEY: 20250816_170736_a45102c4" -ForegroundColor White
Write-Host "   형식: YYYYMMDD_HHMMSS_xxxxxxxx" -ForegroundColor Gray

Write-Host "`n⚡ 빠른 테스트:" -ForegroundColor Cyan
Write-Host "   대시보드 실행: .\scripts\run_velos_dashboard.ps1" -ForegroundColor White
Write-Host "   브라우저 접속: http://localhost:8501" -ForegroundColor White
Write-Host "   REPORT_KEY 입력: 20250816_170736_a45102c4" -ForegroundColor White

Write-Host "`n⚙️ 환경변수 설정 (선택사항):" -ForegroundColor Cyan
Write-Host "   NOTION_TOKEN: Notion API 토큰" -ForegroundColor Gray
Write-Host "   NOTION_DATABASE_ID: Notion 데이터베이스 ID" -ForegroundColor Gray
Write-Host "   SLACK_BOT_TOKEN: Slack 봇 토큰" -ForegroundColor Gray
Write-Host "   NOTION_RESULTID_PROP: Notion 결과 ID 속성명 (기본값: '결과 ID')" -ForegroundColor Gray

Write-Host "`n💡 사용 팁:" -ForegroundColor Cyan
Write-Host "   - 환경변수가 없어도 로컬 파일 검색은 정상 작동" -ForegroundColor Gray
Write-Host "   - 로그 Tail 라인 수를 조절하여 성능 최적화" -ForegroundColor Gray
Write-Host "   - 카테고리별로 파일을 분류하여 보기 편함" -ForegroundColor Gray
Write-Host "   - 검색 결과 요약으로 전체 현황 파악 가능" -ForegroundColor Gray

Write-Host "`n🔧 문제 해결:" -ForegroundColor Cyan
Write-Host "   - Streamlit 설치: pip install streamlit" -ForegroundColor Gray
Write-Host "   - 포트 충돌: 다른 포트 사용 (--server.port 8502)" -ForegroundColor Gray
Write-Host "   - 환경변수: .env 파일 확인" -ForegroundColor Gray
Write-Host "   - 권한 문제: 관리자 권한으로 실행" -ForegroundColor Gray

Write-Host "`n✨ VELOS REPORT_KEY 대시보드 준비 완료!" -ForegroundColor Green
Write-Host "REPORT_KEY 하나로 모든 관련 정보를 한 번에 검색하세요!" -ForegroundColor Yellow



