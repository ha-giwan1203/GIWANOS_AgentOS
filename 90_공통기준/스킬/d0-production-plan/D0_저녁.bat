@echo off
chcp 65001 > nul
title D0 저녁 계획 반영
echo.
echo =====================================================
echo   D0 저녁 계획 반영 (SP3M3 야간 + SD9A01 OUTER)
echo =====================================================
echo.
echo   SP3M3 야간 ERP 생산일 = 오늘
echo   SD9A01 OUTER ERP 생산일 = 내일
echo.
echo   브라우저-less HTTP 모드(--http-only). 마우스·키보드 점유 없음.
echo   중단하려면 Ctrl+C 누르세요.
echo.
pause
echo.
cd /d "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan"
python run.py --session evening --line ALL --http-only
echo.
echo =====================================================
echo   실행 종료 — 결과 확인 후 아무 키나 누르세요.
echo =====================================================
pause
