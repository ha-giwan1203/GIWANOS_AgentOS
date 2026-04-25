@echo off
chcp 65001 >nul
echo ============================================
echo  Flow Chat Collector - One Click
echo ============================================
echo.

REM Chrome 디버깅 모드 실행 (이미 열려있으면 스킵)
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I "chrome.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo [1/3] Chrome 실행 중...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 --user-data-dir="%USERPROFILE%\.flow-chrome-debug" "https://flow.team/main.act"
    echo Chrome 실행 완료. 5초 대기...
    timeout /t 5 /nobreak >nul
) else (
    echo [1/3] Chrome 이미 실행 중. 스킵.
)

echo.
echo [2/3] 채팅방이 열려있는지 확인 중...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] 메시지 수집 시작...
cd /d "%~dp0"
python collector.py --max-scroll 200

echo.
echo ============================================
echo  수집 완료! output 폴더를 확인하세요.
echo ============================================
pause
