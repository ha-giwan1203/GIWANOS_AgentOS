@echo off
cd /d C:\giwanos
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\_ts_evidence.ps1"
exit /b %ERRORLEVEL%
