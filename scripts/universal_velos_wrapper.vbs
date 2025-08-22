' VELOS 범용 숨김 실행 래퍼 v2.0
' 모든 VELOS 스크립트를 완전히 숨겨서 실행
' 사용법: wscript.exe universal_velos_wrapper.vbs "실행할명령어" "작업디렉토리"

If WScript.Arguments.Count < 1 Then
    WScript.Quit(1)
End If

' 실행할 명령어와 작업 디렉토리 받기
Dim command, workDir
command = WScript.Arguments(0)
If WScript.Arguments.Count >= 2 Then
    workDir = WScript.Arguments(1)
Else
    workDir = "C:\giwanos"
End If

' Shell 객체 생성
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 환경변수 설정
Set objEnv = objShell.Environment("Process")
objEnv("PYTHONPATH") = workDir

' 작업 디렉토리 변경
objShell.CurrentDirectory = workDir

' 명령어 실행 (완전 숨김)
' 0 = 완전 숨김, False = 비동기 실행
objShell.Run command, 0, False

' 메모리 정리
Set objShell = Nothing
Set objFSO = Nothing
Set objEnv = Nothing