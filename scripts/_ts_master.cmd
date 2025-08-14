@echo off
cd /d C:\giwanos
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos-run-all.ps1" -NoOpen
exit /b %ERRORLEVEL%
