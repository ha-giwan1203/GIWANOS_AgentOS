' D0_SP3M3_Morning hidden launcher
' schtasks가 wscript로 호출 → 콘솔 0번 표시 → chrome이 자동 OS-foreground
' 세션141 (2026-05-04) 사용자 직접 관찰 후 패치
' 세션143 (2026-05-06) 한글 path 인코딩 mismatch 회피 — WScript.ScriptFullName self-reference 패턴
'   증거: 5/6 07:11 자동 실행 시 wscript는 result=0 리턴했지만 cmd가 한글 path .bat 못 찾아 morning_20260506.log 미생성
'   격리 검증 PASS (한글 path 안의 dummy bat이 self-ref 패턴으로 정상 spawn)
' 짝 bat: run_morning.bat (같은 폴더에 두는 게 전제)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
sh.Run "run_morning.bat", 0, False
