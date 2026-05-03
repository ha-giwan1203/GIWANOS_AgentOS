' D0_SP3M3_Morning_Recover hidden launcher
' schtasks가 wscript로 호출 → 콘솔 0번 표시
' 세션141 (2026-05-04) 사용자 직접 관찰 후 패치
' 짝 bat: run_morning_recover.bat
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c """"C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning_recover.bat""""", 0, False
