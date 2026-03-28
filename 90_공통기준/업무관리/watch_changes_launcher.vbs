' watch_changes_launcher.vbs
' 콘솔 창 없이 watch_changes.py를 백그라운드 실행
' 작업 스케줄러에서 이 파일을 호출

Dim oShell
Set oShell = CreateObject("WScript.Shell")

Dim pythonExe
pythonExe = "C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"

Dim scriptPath
scriptPath = "C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\watch_changes.py"

Dim workDir
workDir = "C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리"

' 0 = 창 숨김, False = 비동기 실행 (스케줄러가 즉시 반환하도록)
oShell.Run "cmd /c set PYTHONUTF8=1 && """ & pythonExe & """ """ & scriptPath & """", 0, False

Set oShell = Nothing
