@echo off
setlocal
set "PYTHONPATH=C:\giwanos"
set "VELOS_DB_WRITE_FORBIDDEN=1"
set "VELOS_ALLOW_BRIDGE=1"
"C:\Users\User\venvs\velos\Scripts\python.exe" "C:\giwanos\scripts\velos_bridge.py"
exit /b %ERRORLEVEL%
