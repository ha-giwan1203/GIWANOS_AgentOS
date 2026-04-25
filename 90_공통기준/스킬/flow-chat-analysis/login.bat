@echo off
chcp 65001 >nul
echo [Flow Collector] Chrome Debug Mode
echo.
echo Chrome을 디버깅 모드로 실행합니다.
echo 로그인이 유지되어 있으면 바로 collect.bat 실행 가능합니다.
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir="%USERPROFILE%\.flow-chrome-debug" "https://flow.team/main.act?detail"
echo.
echo Chrome이 열렸습니다.
echo SP3S03 프로젝트 페이지에서 채팅방을 열어주세요.
echo 채팅방 열린 후 collect.bat을 실행하세요.
echo.
pause
