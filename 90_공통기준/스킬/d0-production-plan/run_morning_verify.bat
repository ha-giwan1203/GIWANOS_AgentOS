@echo off
setlocal
chcp 65001 > nul
title D0_SP3M3_Morning_VERIFY (parse-only)

rem ---------------------------------------------------------
rem 검증용 wrapper — --parse-only 로 Phase 3 selectList 까지만 실행
rem 동작: python run.py --session morning --line SP3M3 --parse-only
rem 목적: batch 인코딩 + 9223 포트 + ERP 로그인 + 엑셀 생성
rem        + ERP 업로드창에 엑셀 첨부 + 서버 파싱(selectList) 검증
rem multiList(DB 저장)/Phase 4-5 미실행 — 운영 영향 없음
rem 로그: 06_생산관리/D0_업로드/logs/verify_YYYYMMDD_HHMMSS.log
rem ---------------------------------------------------------

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTSTAMP=%%i

set LOGDIR=C:\Users\User\Desktop\업무리스트\06_생산관리\D0_업로드\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOGFILE=%LOGDIR%\verify_%DTSTAMP%.log

cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"

echo. >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"
echo [%DTSTAMP%] SP3M3 Morning VERIFY (parse-only) start >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

python run.py --session morning --line SP3M3 --parse-only >> "%LOGFILE%" 2>&1
set RC=%ERRORLEVEL%

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set DTEND=%%i
echo ------------------------------------------------------- >> "%LOGFILE%"
echo [%DTEND%] exit code = %RC% >> "%LOGFILE%"
echo ======================================================= >> "%LOGFILE%"

echo VERIFY DONE — logfile: %LOGFILE%
echo exit code = %RC%

endlocal
exit /b %RC%
