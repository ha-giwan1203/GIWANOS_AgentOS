@echo off
REM usage: velos_write.cmd <room> <body> [user]
setlocal
set PY=python
%PY% "C:\giwanos\scripts\velos_client_write.py" %*
endlocal
