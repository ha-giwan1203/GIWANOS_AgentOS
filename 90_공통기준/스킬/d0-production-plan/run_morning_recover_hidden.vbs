' D0_SP3M3_Morning_Recover hidden launcher
' schtasks가 wscript로 호출 → 콘솔 0번 표시
' 세션141 (2026-05-04) 사용자 직접 관찰 후 패치
' 세션143 (2026-05-06) 한글 path 인코딩 mismatch 회피 — WScript.ScriptFullName self-reference 패턴
' 짝 bat: run_morning_recover.bat (같은 폴더)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
sh.Run "run_morning_recover.bat", 0, False
