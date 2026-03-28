@echo off
setlocal
pushd C:\giwanos
set "PYTHONPATH=C:\giwanos"
"C:\Users\User\venvs\velos\Scripts\python.exe" "C:\giwanos\scripts\velos_report.py"
exit /b %ERRORLEVEL%
