# VELOS PowerShell 숨김 실행 래퍼 v2.0
param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkingDirectory = "C:\giwanos",
    
    [Parameter(Mandatory=$false)]
    [string]$Arguments = ""
)

# 작업 디렉토리 설정
Set-Location $WorkingDirectory
$env:PYTHONPATH = $WorkingDirectory

# 완전 숨김으로 실행
if ($Arguments) {
    Start-Process $Command -ArgumentList $Arguments -WindowStyle Hidden -NoNewWindow
} else {
    Start-Process $Command -WindowStyle Hidden -NoNewWindow
}