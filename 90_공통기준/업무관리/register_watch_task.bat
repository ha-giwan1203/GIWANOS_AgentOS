@echo off
chcp 65001 > nul
REM ============================================================
REM register_watch_task.bat
REM 작업 스케줄러 등록 (재시작 옵션 포함)
REM CMD 창에서 직접 실행하세요 (관리자 권한 불필요)
REM ============================================================

set TASK_NAME=업무리스트_파일감시
set VBS_PATH=C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\watch_changes_launcher.vbs

echo [1/3] 기존 작업 제거...
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

echo [2/3] 작업 등록 중...
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "wscript.exe \"%VBS_PATH%\"" ^
  /sc ONLOGON ^
  /delay 0000:30 ^
  /f

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 등록 실패. 아래 명령을 CMD에서 직접 실행하세요:
    echo   schtasks /create /tn "%TASK_NAME%" /tr "wscript.exe \"%VBS_PATH%\"" /sc ONLOGON /delay 0000:30 /f
    pause
    exit /b 1
)

echo [3/3] 등록 확인:
schtasks /query /tn "%TASK_NAME%" /fo LIST

echo.
echo [완료] 다음 로그인 시 자동 시작됩니다.
echo.
echo 수동 실행:   schtasks /run /tn "%TASK_NAME%"
echo 작업 제거:   schtasks /delete /tn "%TASK_NAME%" /f
echo.
pause
