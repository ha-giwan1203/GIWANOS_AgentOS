# VELOS REPORT_KEY 검색 도구 사용법 안내
# 다양한 방법으로 REPORT_KEY 검색

$ErrorActionPreference = "Stop"

Write-Host "🔍 VELOS REPORT_KEY 검색 도구" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📋 사용 가능한 검색 방법:" -ForegroundColor Cyan

Write-Host "`n1️⃣ 명령줄 검색 (CLI)" -ForegroundColor Yellow
Write-Host "   가장 빠르고 간단한 검색" -ForegroundColor Gray
Write-Host "   명령어: python scripts\velos_search_cli.py <REPORT_KEY>" -ForegroundColor White
Write-Host "   예시: python scripts\velos_search_cli.py 20250816_170736_a45102c4" -ForegroundColor White

Write-Host "`n2️⃣ 웹 인터페이스 (Streamlit)" -ForegroundColor Yellow
Write-Host "   시각적이고 사용하기 쉬운 웹 앱" -ForegroundColor Gray
Write-Host "   명령어: .\scripts\run_velos_search.ps1" -ForegroundColor White
Write-Host "   브라우저: http://localhost:8501" -ForegroundColor White

Write-Host "`n3️⃣ 직접 Python 실행" -ForegroundColor Yellow
Write-Host "   Streamlit 앱을 직접 실행" -ForegroundColor Gray
Write-Host "   명령어: streamlit run scripts\velos_report_search.py" -ForegroundColor White

Write-Host "`n📂 검색되는 파일 범위:" -ForegroundColor Cyan
Write-Host "   📄 로그 파일: data/logs/*.json" -ForegroundColor Gray
Write-Host "   📊 보고서: data/reports/**/*" -ForegroundColor Gray
Write-Host "   🤔 회고: data/reflections/*.json" -ForegroundColor Gray
Write-Host "   🧠 메모리: data/memory/*.json" -ForegroundColor Gray
Write-Host "   📝 세션: data/sessions/*.json" -ForegroundColor Gray
Write-Host "   📸 스냅샷: data/snapshots/**/*" -ForegroundColor Gray
Write-Host "   📋 Notion: DB 검색 링크 제공" -ForegroundColor Gray

Write-Host "`n🔍 검색 예시:" -ForegroundColor Cyan
Write-Host "   REPORT_KEY: 20250816_170736_a45102c4" -ForegroundColor White
Write-Host "   형식: YYYYMMDD_HHMMSS_xxxxxxxx" -ForegroundColor Gray

Write-Host "`n⚡ 빠른 테스트:" -ForegroundColor Cyan
Write-Host "   CLI 테스트: python scripts\velos_search_cli.py 20250816_170736_a45102c4" -ForegroundColor White
Write-Host "   웹 앱 실행: .\scripts\run_velos_search.ps1" -ForegroundColor White

Write-Host "`n💡 팁:" -ForegroundColor Cyan
Write-Host "   - CLI는 빠른 검색에 적합" -ForegroundColor Gray
Write-Host "   - 웹 앱은 시각적 결과와 상세 정보에 적합" -ForegroundColor Gray
Write-Host "   - Notion DB는 별도로 검색 필요" -ForegroundColor Gray

Write-Host "`n✨ VELOS REPORT_KEY 검색 도구 준비 완료!" -ForegroundColor Green
