Set WshShell = CreateObject("WScript.Shell")
cmd = """" & "%ProgramFiles%\PowerShell\7\pwsh.exe" & """" & _
      " -NoProfile -ExecutionPolicy Bypass -File """"C:\giwanos\scripts\Start-Velos.ps1"""""
WshShell.Run cmd, 0
