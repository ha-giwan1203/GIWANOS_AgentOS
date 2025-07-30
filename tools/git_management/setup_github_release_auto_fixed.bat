@echo off
chcp 65001 >nul

SET TARGET_DIR=C:\giwanos\github_release_bundle

IF NOT EXIST "%TARGET_DIR%" (
    echo 📁 [자동 생성] %TARGET_DIR%
    mkdir "%TARGET_DIR%"
)

cd /d "%TARGET_DIR%"

IF EXIST ".git\index.lock" (
    echo ⚠️ Git lock 파일 감지됨. 자동 삭제 중...
    del /f /q ".git\index.lock"
)

IF NOT EXIST ".git" (
    echo 🔧 Git 저장소 초기화 중...
    git init
)

git remote remove origin 2>nul
git remote add origin https://github.com/YOUR_ID/YOUR_REPO.git

REM 릴리즈 실행
python push_github_release.py

pause
