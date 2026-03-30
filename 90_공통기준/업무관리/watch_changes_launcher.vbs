' watch_changes_launcher.vbs
' Launches watch_changes.py silently in the background (no console window)
' Called by Windows Task Scheduler

Dim oShell
Set oShell = CreateObject("WScript.Shell")

Dim pythonExe
pythonExe = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

' Derive script path from this launcher's own location (avoids Korean path encoding issues)
Dim launcherDir
launcherDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

Dim scriptPath
scriptPath = launcherDir & "watch_changes.py"

' 0 = hidden window, False = async (task scheduler returns immediately)
oShell.Run "cmd /c set PYTHONUTF8=1 && """ & pythonExe & """ """ & scriptPath & """", 0, False

Set oShell = Nothing
