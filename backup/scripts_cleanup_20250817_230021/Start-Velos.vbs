Set WshShell = CreateObject("WScript.Shell")
' 절대경로 필수. 공백 있으면 따옴표로 감쌈.
cmd = "powershell.exe -ExecutionPolicy Bypass -File ""C:\giwanos\scripts\Start-Velos.ps1"""
WshShell.Run cmd, 0, False   ' 0 = 숨김, False = 비동기(스케줄러가 안 잡고 있음)
