@echo off
echo ============================================
echo  Flow.team 채팅 수집기 - 로그인 모드
echo ============================================
echo.
echo 전용 브라우저가 열립니다.
echo Flow.team에 로그인 후 Enter를 누르세요.
echo.
cd /d "%~dp0"
python collector.py --login
pause
