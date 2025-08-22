' VELOS Daily Report 실행 - 완전 숨김 실행
' 생성일: 2025-08-21 23:22:10

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 작업 디렉토리 및 환경 설정
strWorkingDir = "C:\giwanos"
objShell.CurrentDirectory = strWorkingDir

Set objEnv = objShell.Environment("Process")
objEnv("PYTHONPATH") = strWorkingDir

' 스크립트 실행 (완전 숨김)
objShell.Run "python .\scripts\velos_daily_report.py", 0, False

' 메모리 정리
Set objShell = Nothing
Set objFSO = Nothing
Set objEnv = Nothing