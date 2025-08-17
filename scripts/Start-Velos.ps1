#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

# 루트 고정
$Root = 'C:\giwanos'
Set-Location $Root

# 싱글톤 락(파워셸 레벨, 이중 안전장치)
$Lock = Join-Path $Root 'data\.velos.ps1.lock'
if (Test-Path $Lock) { exit 0 }
New-Item -ItemType File -Path $Lock -Force | Out-Null

# 로그 디렉토리
$LogDir = Join-Path $Root 'data\logs'
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$Log = Join-Path $LogDir ("launcher_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

try {
  # venv 연결: .venv_link 있으면 그걸 우선
  $venv = $null
  $venvLink = Join-Path $Root '.venv_link'
  if (Test-Path $venvLink) { $venv = Get-Content $venvLink -ErrorAction SilentlyContinue }
  if (-not $venv) { $venv = Join-Path $Root '.venv' }
  $python = Join-Path $venv 'Scripts\python.exe'
  if (-not (Test-Path $python)) { $python = 'python' }  # 최후의 보루

  # PYTHONPATH 등 환경 변수 필요하면 여기서 고정
  $env:PYTHONPATH = $Root
  $env:VELOS_ROOT = $Root

  # 마스터 루프 실행 (파워셸은 숨김, 파이썬 출력만 로그로)
  $entry = Join-Path $Root 'scripts\velos_master_scheduler.py'
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $python
  $psi.WorkingDirectory = $Root
  $psi.Arguments = "`"$entry`" --singleton --log-dir `"$LogDir`""
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true

  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()

  $out | Out-File -FilePath $Log -Encoding UTF8 -Append
  if ($err) { "[ERR] " + $err | Out-File -FilePath $Log -Encoding UTF8 -Append }
}
finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
