' VELOS Bridge 완전 숨김 실행 스크립트
' 이 스크립트는 Python 프로그램을 완전히 숨겨서 실행합니다

Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 작업 디렉토리 설정
strWorkingDir = "C:\giwanos"
strPythonPath = "C:\giwanos"

' 환경변수 설정
Set objEnv = objShell.Environment("Process")
objEnv("PYTHONPATH") = strPythonPath

' 현재 디렉토리 변경 및 Python 스크립트 실행
' 0 = 완전 숨김, False = 실행 완료까지 기다리지 않음
objShell.CurrentDirectory = strWorkingDir
objShell.Run "python .\scripts\velos_bridge.py", 0, False

' 메모리 정리
Set objShell = Nothing
Set objFSO = Nothing
Set objEnv = Nothing