@echo off
REM check_watch_alive.bat — watch_changes.py 프로세스 감시 + 자동 재시작
REM 스케줄러에 5분 간격으로 등록하여 사용

set LOCK_FILE=C:\Users\User\Desktop\업무리스트\.watch.lock
set LAUNCHER=C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\watch_changes_launcher.vbs

REM lock 파일이 없으면 프로세스 미실행 → 시작
if not exist "%LOCK_FILE%" (
    echo [%date% %time%] watch_changes not running. Starting...
    wscript.exe "%LAUNCHER%"
    exit /b 0
)

REM lock 파일에서 PID 읽기
set /p PID=<"%LOCK_FILE%"

REM PID가 살아있는지 확인
tasklist /fi "PID eq %PID%" 2>nul | find "%PID%" >nul
if errorlevel 1 (
    REM 프로세스 죽어있음 → lock 제거 후 재시작
    echo [%date% %time%] PID %PID% dead. Removing lock and restarting...
    del "%LOCK_FILE%" 2>nul
    wscript.exe "%LAUNCHER%"
) else (
    REM 살아있음 → 아무것도 안 함
    REM echo [%date% %time%] PID %PID% alive. OK.
)
