' D0_SP3M3_Morning hidden launcher
' schtasks가 wscript로 호출 → 콘솔 0번 표시 → chrome이 자동 OS-foreground
' 세션141 (2026-05-04) 사용자 직접 관찰 후 패치
' 짝 bat: run_morning.bat (직접 실행 시는 콘솔 표시 정상)
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c """"C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning.bat""""", 0, False
