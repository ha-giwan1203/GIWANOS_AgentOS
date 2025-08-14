@echo off
cd /d C:\giwanos
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\cursor_evidence_check.ps1"
exit /b %ERRORLEVEL%
