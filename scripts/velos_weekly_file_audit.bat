@echo off
REM VELOS Weekly File Audit - 런타임 트레이스 + 리스크 감사
REM 매주 일요일 새벽 3:30에 자동 실행

echo [VELOS] Weekly File Audit 시작 - %date% %time%

REM 1단계: 런타임 트레이스 + 매니페스트 동기화
echo [VELOS] 1단계: 런타임 트레이스 실행
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\giwanos\scripts\run_runtime_trace_and_sync.ps1"
if %errorlevel% neq 0 (
    echo [VELOS] 런타임 트레이스 실패
    exit /b 1
)

REM 2단계: 파일 사용성 리스크 감사
echo [VELOS] 2단계: 리스크 감사 실행
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\giwanos\scripts\run_file_usage_risk_audit.ps1"
if %errorlevel% neq 0 (
    echo [VELOS] 리스크 감사 실패
    exit /b 1
)

echo [VELOS] Weekly File Audit 완료 - %date% %time%
