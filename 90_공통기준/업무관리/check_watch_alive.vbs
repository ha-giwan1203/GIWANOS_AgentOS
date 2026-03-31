' check_watch_alive.vbs — 창 없이 헬스체크 bat 실행
Set oShell = CreateObject("WScript.Shell")
oShell.Run "cmd /c ""C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\check_watch_alive.bat""", 0, True
Set oShell = Nothing
