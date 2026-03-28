# [ACTIVE] VELOS 브리지 시작 시스템 - VELOS 브리지 시작 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

$ErrorActionPreference='Stop'
Set-Location -Path 'C:\giwanos'           # Start in이 비어도 안전
$env:PYTHONPATH = 'C:\giwanos'            # 임포트 경로 확정

# 로그 디렉터리 설정 (통합된 경로 사용)
$logDir = 'C:\giwanos\data\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("bridge_" + (Get-Date -Format 'yyyyMMdd') + ".log")

# 환경변수 설정
$env:VELOS_ROOT = 'C:\giwanos'
$env:VELOS_LOG_PATH = $logDir

# Python 실행 (venv 우선, fallback 지원)
$venv = 'C:\Users\User\venvs\velos\Scripts'
if (Test-Path "$venv\python.exe") {
  Write-Host "VELOS 브리지 시작 (venv 사용): $venv" -ForegroundColor Green
  & "$venv\python.exe" .\scripts\velos_bridge.py *>> $log
} else {
  Write-Host "VELOS 브리지 시작 (시스템 Python 사용)" -ForegroundColor Yellow
  python .\scripts\velos_bridge.py *>> $log
}
