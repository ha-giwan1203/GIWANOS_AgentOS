# C:\giwanos\scripts\velos_master_loop_wrapper.ps1
# 목적: 콘솔창 없이 VELOS 마스터 루프/모니터를 백그라운드 실행

$ErrorActionPreference = 'SilentlyContinue'
Set-Location 'C:\giwanos'

# 가상환경 pythonw.exe (콘솔 없는 런타임)
$pyw = 'C:\Users\User\venvs\velos\Scripts\pythonw.exe'

# 1) 모니터(Streamlit) 서버가 없으면 띄움 (headless, 조용히)
$port = 8502
$up = Test-NetConnection -ComputerName 'localhost' -Port $port -InformationLevel Quiet
if (-not $up) {
  $argsMon = @(
    '-m','streamlit','run','modules\reports\monitor.py',
    '--server.address','localhost',
    '--server.port',"$port",
    '--server.headless','true',
    '--logger.level','error'
  )
  Start-Process -FilePath $pyw -ArgumentList $argsMon -WindowStyle Hidden
}

# 2) 마스터 루프(필요 시 경로/파일명 맞게) 조용히 실행
$masterScript = 'scripts\velos_master_loop.py'
if (Test-Path $masterScript) {
  Start-Process -FilePath $pyw -ArgumentList @($masterScript) -WindowStyle Hidden
}

exit 0
