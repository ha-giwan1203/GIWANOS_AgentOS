' =========================================================
' VELOS 완전 숨김 실행 스크립트 v2.0 - 실행창 완전 제거
' PowerShell 7.x 최적화 + 완전 백그라운드 실행
' =========================================================

Option Explicit

Dim WshShell, fso, VELOS_ROOT, logPath, logFile
Dim cmd, processInfo, startTime

' 상수 정의
VELOS_ROOT = "C:\giwanos"

' 객체 생성
Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

' 로그 파일 설정
logPath = VELOS_ROOT & "\data\logs\velos_hidden_" & Year(Now) & Right("0" & Month(Now), 2) & Right("0" & Day(Now), 2) & ".log"

' 로그 디렉토리 생성
If Not fso.FolderExists(VELOS_ROOT & "\data\logs") Then
    fso.CreateFolder(VELOS_ROOT & "\data\logs")
End If

' 로그 기록 함수
Sub WriteLog(message, level)
    On Error Resume Next
    Dim timestamp, logEntry
    timestamp = FormatDateTime(Now, vbGeneralDate)
    logEntry = "[" & timestamp & "] [" & level & "] " & message
    
    Set logFile = fso.OpenTextFile(logPath, 8, True) ' 8 = Append mode
    logFile.WriteLine logEntry
    logFile.Close
    Set logFile = Nothing
    On Error GoTo 0
End Sub

' 시작 로그
WriteLog "VELOS 완전 숨김 스케줄러 시작", "INFO"

' 싱글톤 체크
Dim lockFile
lockFile = VELOS_ROOT & "\data\.velos_hidden.lock"

If fso.FileExists(lockFile) Then
    Dim lockFileObj, lockTime, currentTime, timeDiff
    Set lockFileObj = fso.GetFile(lockFile)
    lockTime = lockFileObj.DateLastModified
    currentTime = Now
    timeDiff = DateDiff("n", lockTime, currentTime) ' 분 단위 차이
    
    If timeDiff < 10 Then
        WriteLog "이미 실행 중 (락 파일 존재, " & timeDiff & "분 전)", "INFO"
        WScript.Quit 0
    End If
End If

' 락 파일 생성
Set lockFile = fso.CreateTextFile(lockFile, True)
lockFile.WriteLine "VELOS Hidden Scheduler Lock - " & Now
lockFile.Close
Set lockFile = Nothing

WriteLog "싱글톤 락 생성 완료", "INFO"

' PowerShell 7.x 병렬 스케줄러 실행 명령
' 완전 숨김 모드로 PowerShell 7 사용
cmd = "pwsh.exe -NoProfile -NoLogo -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass " & _
      "-Command ""& { " & _
      "$env:PYTHONPATH='C:\giwanos'; " & _
      "$env:VELOS_ROOT='C:\giwanos'; " & _
      "Set-Location 'C:\giwanos'; " & _
      "try { " & _
      "  .\scripts\Invoke-VelosParallel.ps1 -ThrottleLimit 3 2>&1 | Out-File -FilePath 'data\logs\parallel_output.log' -Append -Encoding UTF8; " & _
      "  if ($LASTEXITCODE -eq 0) { " & _
      "    'SUCCESS: VELOS 병렬 스케줄러 완료' | Out-File -FilePath 'data\logs\vbs_success.log' -Append -Encoding UTF8 " & _
      "  } else { " & _
      "    'ERROR: 종료코드 ' + $LASTEXITCODE | Out-File -FilePath 'data\logs\vbs_error.log' -Append -Encoding UTF8 " & _
      "  } " & _
      "} catch { " & _
      "  'EXCEPTION: ' + $_.Exception.Message | Out-File -FilePath 'data\logs\vbs_error.log' -Append -Encoding UTF8 " & _
      "} finally { " & _
      "  Remove-Item 'data\.velos_hidden.lock' -Force -ErrorAction SilentlyContinue " & _
      "} " & _
      "}"""

WriteLog "실행 명령 준비 완료", "INFO"
WriteLog "명령: " & Left(cmd, 100) & "...", "DEBUG"

' 완전 숨김 모드로 실행
' 0 = 창 숨김, True = 프로세스 완료까지 대기 (하지만 백그라운드)
startTime = Now

On Error Resume Next
WshShell.Run cmd, 0, True

' 오류 체크
If Err.Number <> 0 Then
    WriteLog "PowerShell 실행 오류: " & Err.Description & " (코드: " & Err.Number & ")", "ERROR"
    ' 락 파일 정리
    If fso.FileExists(VELOS_ROOT & "\data\.velos_hidden.lock") Then
        fso.DeleteFile VELOS_ROOT & "\data\.velos_hidden.lock"
    End If
    WScript.Quit 1
Else
    Dim duration
    duration = DateDiff("s", startTime, Now)
    WriteLog "PowerShell 병렬 스케줄러 실행 완료 (소요시간: " & duration & "초)", "INFO"
End If

On Error GoTo 0

' 정리 작업
WriteLog "VELOS 숨김 스케줄러 종료", "INFO"

' 객체 정리
Set WshShell = Nothing
Set fso = Nothing

' 조용히 종료
WScript.Quit 0