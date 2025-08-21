# [ACTIVE] VELOS 완전 숨김 실행 스크립트 - 콘솔 창 완전 제거
# 백그라운드 전용 실행, 모든 출력 억제
param(
    [string]$LogFile = ""
)

$ErrorActionPreference = 'SilentlyContinue'

# 루트 고정
$Root = 'C:\giwanos'
Set-Location $Root -ErrorAction SilentlyContinue

# 싱글톤 락
$Lock = Join-Path $Root 'data\.velos.ps1.lock'
if (Test-Path $Lock) { 
    exit 0 
}
New-Item -ItemType File -Path $Lock -Force -ErrorAction SilentlyContinue | Out-Null

# 로그 디렉토리
$LogDir = Join-Path $Root 'data\logs'
New-Item -ItemType Directory -Path $LogDir -Force -ErrorAction SilentlyContinue | Out-Null
$Log = if ($LogFile) { $LogFile } else { Join-Path $LogDir ("silent_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log") }

try {
  # venv 연결
  $venv = $null
  $venvLink = Join-Path $Root '.venv_link'
  if (Test-Path $venvLink) { 
      $venv = Get-Content $venvLink -ErrorAction SilentlyContinue 
  }
  if (-not $venv) { $venv = Join-Path $Root '.venv' }
  $python = Join-Path $venv 'Scripts\python.exe'
  if (-not (Test-Path $python)) { $python = 'python' }

  # 환경 변수 설정
  $env:PYTHONPATH = $Root
  $env:VELOS_ROOT = $Root

  # 마스터 루프 실행
  $entry = Join-Path $Root 'scripts\velos_master_scheduler.py'
  
  # 완전 숨김 모드 매개변수
  $args = @("`"$entry`"", "--singleton")

  # 완전 숨김 프로세스 실행
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $python
  $psi.WorkingDirectory = $Root
  $psi.Arguments = $args -join ' '
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.CreateNoWindow = $true
  $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()

  # 로그만 기록, 콘솔 출력 없음
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "[$timestamp] VELOS Silent execution completed (Exit: $($p.ExitCode))" | Out-File -FilePath $Log -Encoding UTF8 -Append
  if ($out) { "[$timestamp] OUT: $out" | Out-File -FilePath $Log -Encoding UTF8 -Append }
  if ($err) { "[$timestamp] ERR: $err" | Out-File -FilePath $Log -Encoding UTF8 -Append }
  
}
catch {
  # 오류도 조용히 로그에만 기록
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "[$timestamp] ERROR: $($_.Exception.Message)" | Out-File -FilePath $Log -Encoding UTF8 -Append -ErrorAction SilentlyContinue
}
finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}

# 완전 조용히 종료 (아무 출력 없음)
exit 0