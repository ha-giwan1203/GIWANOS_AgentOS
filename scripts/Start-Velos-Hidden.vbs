' =========================================================
' VELOS 운영 철학 선언문
' 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
' 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
' 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
' 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
' 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
' 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
' 7) 구조 기반 판단: 프로젝트 기준으로만 판단 (추측 금지)
' 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
' 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
' 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
' =========================================================

' VELOS 마스터 스케줄러 숨겨진 실행 스크립트
' Windows Task Scheduler에서 5분마다 실행하여 VELOS 작업을 관리

Option Explicit

Dim WshShell, cmd, VELOS_ROOT, scriptPath, logPath
Dim fso, logFile

' VELOS 루트 경로 설정
VELOS_ROOT = "C:\giwanos"

' 파일 시스템 객체 생성
Set fso = CreateObject("Scripting.FileSystemObject")

' 로그 파일 경로
logPath = VELOS_ROOT & "\data\logs\velos_vbs.log"

' 로그 기록 함수
Sub WriteLog(message)
    On Error Resume Next
    Dim timestamp
    timestamp = Now()
    logFile.WriteLine "[" & timestamp & "] " & message
    logFile.Close
    Set logFile = fso.OpenTextFile(logPath, 8, True) ' 8 = ForAppending, True = Create if not exists
End Sub

' 로그 파일 초기화
Set logFile = fso.OpenTextFile(logPath, 8, True)

' 시작 로그
WriteLog "VELOS VBS 스크립트 시작"

' 스크립트 경로 확인
scriptPath = VELOS_ROOT & "\scripts\Start-Velos.ps1"

If Not fso.FileExists(scriptPath) Then
    WriteLog "오류: Start-Velos.ps1 파일을 찾을 수 없음: " & scriptPath
    WScript.Quit 1
End If

WriteLog "스크립트 경로 확인됨: " & scriptPath

' WScript.Shell 객체 생성
Set WshShell = CreateObject("WScript.Shell")

' PowerShell 명령 구성
' 절대경로 필수. 공백 있으면 따옴표로 감쌈.
cmd = "powershell.exe -NoProfile -NoLogo -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & VELOS_ROOT & "\scripts\Start-Velos-Silent.ps1"""

WriteLog "실행 명령: " & cmd

' 숨겨진 모드로 실행
' 0 = 숨김, False = 비동기(스케줄러가 안 잡고 있음)
WshShell.Run cmd, 0, False

WriteLog "VELOS 마스터 스케줄러 실행 완료"

' 정리
Set WshShell = Nothing
Set fso = Nothing
logFile.Close
Set logFile = Nothing
