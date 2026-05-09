' D0_SP3M3_Evening hidden launcher
' schtasks가 wscript로 호출 → 콘솔 0번 표시 → chrome이 자동 OS-foreground
' 짝 bat: run_evening.bat (같은 폴더에 두는 게 전제)
' 한글 path 인코딩 mismatch 회피 — WScript.ScriptFullName self-reference 패턴 (morning과 동일 레시피)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
sh.Run "run_evening.bat", 0, False
