' [ACTIVE] VELOS 자동 정리 워처 숨겨진 실행
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ""C:\giwanos\scripts\velos_autoclean.ps1""", 0, False
