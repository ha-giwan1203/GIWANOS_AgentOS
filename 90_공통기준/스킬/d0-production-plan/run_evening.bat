@echo off
setlocal
chcp 65001 > nul
title D0_SP3M3_Evening (auto)

rem ---------------------------------------------------------
rem Windows 작업 스케줄러용 래퍼 (저녁 야간 + OUTER D+1 자동 등록)
rem 실행: 매주 월~금 (요일·시간은 schtasks /create로 결정 — 세션151 default 18:50)
rem 동작: python run.py --session evening
rem        - SP3M3 야간 (ERP 생산일 = 오늘)
rem        - SD9A01 OUTER D+1 (ERP 생산일 = 내일)
rem 로그: 06_생산관리/D0_업로드/logs/evening_YYYYMMDD.log
rem ---------------------------------------------------------

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTSTAMP=%%i
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set YMD=%%i

set LOGDIR=C:\Users\User\Desktop\업무리스트\06_생산관리\D0_업로드\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\evening_%YMD%.log

cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"

echo. >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo [%DTSTAMP%] D0 Evening auto-run start >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

python run.py --session evening >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTEND=%%i
echo ------------------------------------------------------- >> "%LOGFILE%"
echo [%DTEND%] exit code = %RC% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

endlocal
exit /b %RC%
