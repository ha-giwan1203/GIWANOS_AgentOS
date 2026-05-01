@echo off
setlocal
chcp 65001 > nul
title D0_SP3M3_Morning_API_COMPARE

rem ---------------------------------------------------------
rem P6 비교 검증 wrapper — 매일 1회 api 모드 1건 PoC
rem 동작: python compare_modes.py
rem 목적: 화면 모드 morning(07:11) 후 별도 시간(예: 07:30)에 api 모드 1건 PoC + DELETE 정리
rem        1주 누적 PASS 시 chain 적용 (run_morning.bat에 --api-mode 추가)
rem 안전 가드:
rem   - sendMesFlag='Y' 절대 호출 안 함 (api_rank_batch 내부 강제)
rem   - 1건만 + DELETE 정리 try/finally
rem   - exit code 0 = PASS, 4 = FAIL
rem 로그: 06_생산관리/D0_업로드/logs/api_p6_compare_YYYYMMDD_HHMMSS.log
rem state: 90_공통기준/스킬/d0-production-plan/state/compare_YYYYMMDD_HHMMSS.json
rem ---------------------------------------------------------

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTSTAMP=%%i

set LOGDIR=C:\Users\User\Desktop\업무리스트\06_생산관리\D0_업로드\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\compare_wrap_%DTSTAMP%.log

cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"

echo. >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo [%DTSTAMP%] D0 SP3M3 P6 COMPARE start >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

python compare_modes.py >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTEND=%%i
echo ------------------------------------------------------- >> "%LOGFILE%"
echo [%DTEND%] exit code = %RC% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

echo COMPARE DONE — logfile: %LOGFILE%
echo exit code = %RC%

endlocal
exit /b %RC%
