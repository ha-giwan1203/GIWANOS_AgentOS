@echo off
chcp 65001 >nul
echo ============================================
echo  Flow Collector - Chrome Debug Mode
echo ============================================
echo.
echo Chrome을 디버깅 모드로 실행합니다.
echo Flow.team에 로그인한 후 collect.bat을 실행하세요.
echo.
echo [주의] 기존 Chrome이 열려있으면 먼저 닫아주세요.
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.flow-chrome-debug" https://flow.team
echo.
echo Chrome이 열렸습니다.
echo 1. Flow.team에 카카오 계정으로 로그인하세요.
echo 2. 로그인 완료 후 collect.bat을 실행하세요.
echo.
pause
