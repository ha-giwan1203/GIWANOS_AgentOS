@echo off
chcp 65001 >nul
echo Chrome을 정상 종료합니다 (로그인 세션 유지)...
taskkill /IM chrome.exe >nul 2>&1
echo 완료. 다음 실행 시 로그인이 유지됩니다.
timeout /t 3
