@echo off
setlocal
pushd C:\giwanos
"C:\Users\User\venvs\velos\Scripts\python.exe" "C:\giwanos\scripts\backup_velos_db.py"
exit /b %ERRORLEVEL%


