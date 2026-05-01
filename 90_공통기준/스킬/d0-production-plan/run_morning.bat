@echo off
setlocal
chcp 65001 > nul
title D0_SP3M3_Morning (auto)

rem ---------------------------------------------------------
rem Windows 작업 스케줄러용 래퍼
rem 실행: 매주 월~토 07:11 KST (세션133 변경)
rem 동작: python run.py --session morning --line SP3M3 --api-mode
rem        (세션133 chain 활성 — 옵션 A 하이브리드, rank 호출은 requests 직접 POST.
rem         final_save Phase 5는 화면 모드 유지. 회귀 시 --api-mode 1줄 제거하면 화면 모드 fallback)
rem 로그: 06_생산관리/D0_업로드/logs/morning_YYYYMMDD.log
rem ---------------------------------------------------------

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTSTAMP=%%i
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set YMD=%%i

set LOGDIR=C:\Users\User\Desktop\업무리스트\06_생산관리\D0_업로드\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\morning_%YMD%.log

cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"

echo. >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo [%DTSTAMP%] SP3M3 Morning auto-run start >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

python run.py --session morning --line SP3M3 --api-mode >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTEND=%%i
echo ------------------------------------------------------- >> "%LOGFILE%"
echo [%DTEND%] exit code = %RC% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

endlocal
exit /b %RC%
