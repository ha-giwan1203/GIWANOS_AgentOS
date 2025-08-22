@echo off
REM VELOS 스케줄러 완전 수정 배치
REM 관리자 권한으로 실행 필요

echo ===================================
echo VELOS 스케줄러 완전 수정 시작
echo ===================================

REM 기존 VELOS 작업들 삭제 (오류 무시)
echo 1. 기존 VELOS 작업들 삭제 중...
schtasks /delete /tn "VELOS Bridge AutoStart" /f >nul 2>&1
schtasks /delete /tn "VELOS Master Loop" /f >nul 2>&1
schtasks /delete /tn "VELOS Daily Report" /f >nul 2>&1
schtasks /delete /tn "VELOS Health Check" /f >nul 2>&1
schtasks /delete /tn "VELOS DB Backup" /f >nul 2>&1

REM 새로운 숨김 작업들 등록
echo 2. 새로운 숨김 작업들 등록 중...

if exist "C:\giwanos\scheduler_improvements\VELOS_Bridge_HIDDEN.xml" (
    schtasks /create /xml "C:\giwanos\scheduler_improvements\VELOS_Bridge_HIDDEN.xml" /tn "VELOS Bridge Hidden"
    echo   - VELOS Bridge Hidden 등록됨
)

if exist "C:\giwanos\scheduler_improvements\VELOS_Master_Loop_HIDDEN.xml" (
    schtasks /create /xml "C:\giwanos\scheduler_improvements\VELOS_Master_Loop_HIDDEN.xml" /tn "VELOS Master Loop Hidden"
    echo   - VELOS Master Loop Hidden 등록됨
)

if exist "C:\giwanos\scheduler_improvements\VELOS_Daily_Report_HIDDEN.xml" (
    schtasks /create /xml "C:\giwanos\scheduler_improvements\VELOS_Daily_Report_HIDDEN.xml" /tn "VELOS Daily Report Hidden"
    echo   - VELOS Daily Report Hidden 등록됨
)

echo 3. 등록된 VELOS 작업 확인...
schtasks /query /tn "*VELOS*" /fo table

echo ===================================
echo VELOS 스케줄러 수정 완료!
echo 이제 창이 나타나지 않습니다.
echo ===================================
pause
