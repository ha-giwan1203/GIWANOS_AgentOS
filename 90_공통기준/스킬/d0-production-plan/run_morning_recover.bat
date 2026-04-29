@echo off
setlocal
chcp 65001 > nul
title D0_SP3M3_Morning_Recover (verify+autoretry)

rem ---------------------------------------------------------
rem D0 morning 사후 검증 + 자동 재실행 wrapper
rem 의제: debate_20260429_121732_3way Round 1 합의 (pass_ratio 1.00)
rem 호출: 사용자가 schtasks /create로 07:30 등록 (morning 20분 후)
rem 목적: morning 실행 결과 검증 → 실패 시 원인 분류 → RETRY_OK 백오프 / RETRY_BLOCK·NO 즉시 알림
rem 로그: 06_생산관리/D0_업로드/logs/recover_YYYYMMDD_HHMMSS.log
rem ---------------------------------------------------------

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTSTAMP=%%i

set LOGDIR=C:\Users\User\Desktop\업무리스트\06_생산관리\D0_업로드\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\recover_%DTSTAMP%.log

cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"

echo. >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo [%DTSTAMP%] D0 SP3M3 Morning Recover start >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

python verify_run.py --session morning --line SP3M3 >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTEND=%%i
echo ------------------------------------------------------- >> "%LOGFILE%"
echo [%DTEND%] verify_run exit code = %RC% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

echo RECOVER DONE — logfile: %LOGFILE%
echo exit code = %RC%

endlocal
exit /b %RC%
