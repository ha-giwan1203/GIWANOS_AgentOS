
@echo off
setlocal

REM 경로 설정 (지완 마스터 설치 위치)
set TARGET_DIR=C:\giwanos
set PATCH_DIR=%~dp0GIWANOS_ChangedOnly_Sorted

echo ✅ GIWANOS 패치 적용 시작...

REM 루트 파일 덮어쓰기
echo 🔄 루트 파일 덮어쓰기...
xcopy /Y /Q "%PATCH_DIR%\root\*" "%TARGET_DIR%\"

REM 서브폴더 파일 덮어쓰기
echo 🔄 하위 폴더 파일 덮어쓰기...
xcopy /Y /Q /E "%PATCH_DIR%\subfolders\*" "%TARGET_DIR%\"

echo ✅ 패치 적용 완료!
pause
