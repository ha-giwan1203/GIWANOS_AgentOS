Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\giwanos\scripts\velos_master_loop_wrapper.ps1""", 0, True
