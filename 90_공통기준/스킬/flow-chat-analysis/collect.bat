@echo off
chcp 65001 >nul
echo ============================================
echo  Flow Collector - Collect Messages
echo ============================================
echo.
echo Chrome 디버깅 모드에 연결하여 채팅 메시지를 수집합니다.
echo [주의] login.bat으로 Chrome이 열려있어야 합니다.
echo.
cd /d "%~dp0"
python collector.py
pause
