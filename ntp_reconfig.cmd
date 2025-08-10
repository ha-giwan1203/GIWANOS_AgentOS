reg add "HKLM\SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient" /v SpecialPollInterval /t REG_DWORD /d 3600 /f
w32tm /config /manualpeerlist:"time.windows.com,0x9 time.cloudflare.com,0x9 time.google.com,0x9" /syncfromflags:manual /update
net stop w32time
net start w32time
w32tm /resync
