@echo off
chcp 65001 >nul
title Claude Code
cd /d "%~dp0..\.."
call claude %*
echo.
echo [Claude Code closed] Press any key to close this window.
pause >nul
