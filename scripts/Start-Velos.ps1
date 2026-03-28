# [ACTIVE] VELOS 시작 스크립트 - 시스템 초기화 및 실행
#Requires -Version 7.0
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

param(
    [switch]$Verbose = $false,
    [switch]$Background = $false,
    [switch]$KeepOutput = $false,
    [switch]$DryRun = $false,
    [string]$LogFile = "",
    [string]$ForceJob = ""
)

$ErrorActionPreference = 'Stop'

# 루트 고정
$Root = 'C:\giwanos'
Set-Location $Root

# 싱글톤 락(파워셸 레벨, 이중 안전장치)
$Lock = Join-Path $Root 'data\.velos.ps1.lock'
if (Test-Path $Lock) { 
    Write-Host "[WARN] 다른 VELOS 인스턴스가 실행 중입니다. 종료합니다." -ForegroundColor Yellow
    exit 0 
}
New-Item -ItemType File -Path $Lock -Force | Out-Null

# 로그 디렉토리
$LogDir = Join-Path $Root 'data\logs'
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$Log = if ($LogFile) { $LogFile } else { Join-Path $LogDir ("launcher_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log") }

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
  
  # 매개변수 구성
  $args = @("`"$entry`"")
  
  if ($Verbose) {
      $args += "--verbose"
  }
  
  if ($DryRun) {
      $args += "--dry-run"
  }
  

  
  if ($ForceJob) {
      $args += "--force"
      $args += $ForceJob
  }
  
  $args += "--singleton"
  $args += "--log-dir"
  $args += "`"$LogDir`""

  if (-not $Background) {
      Write-Host "=== VELOS 마스터 스케줄러 실행 ===" -ForegroundColor Yellow
  Write-Host "Python: $python" -ForegroundColor Cyan
  Write-Host "Arguments: $($args -join ' ')" -ForegroundColor Cyan
      Write-Host "Log: $Log" -ForegroundColor Cyan
  }

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $python
  $psi.WorkingDirectory = $Root
  $psi.Arguments = $args -join ' '
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true

  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()

  # PowerShell 7의 향상된 JSON 로깅
  $logEntry = @{
      timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
      exitCode = $p.ExitCode
      output = $out
      error = $err
  }
  ($logEntry | ConvertTo-Json -Depth 3) | Out-File -FilePath $Log -Encoding UTF8 -Append
  # 에러 로그는 위의 JSON 구조에 통합됨
  
  if ($p.ExitCode -eq 0) {
      if (-not $Background) {
          Write-Host "[SUCCESS] VELOS 마스터 스케줄러 실행 완료" -ForegroundColor Green
      }
      
      if (-not $Background) {
          Write-Host "`n=== VELOS 출력 ===" -ForegroundColor Cyan
          Write-Host $out
          if ($err) {
              Write-Host "`n=== 오류 출력 ===" -ForegroundColor Red
              Write-Host $err
          }
          Write-Host "=== 출력 끝 ===" -ForegroundColor Cyan
      }
      
      if (-not $KeepOutput -and -not $LogFile) {
          Remove-Item $Log -Force -ErrorAction SilentlyContinue
          if (-not $Background) {
              Write-Host "[CLEANUP] 임시 로그 파일 삭제됨" -ForegroundColor Gray
          }
      }
  } else {
      Write-Host "[ERROR] VELOS 마스터 스케줄러 실행 실패 (Exit Code: $($p.ExitCode))" -ForegroundColor Red
      Write-Host "로그 파일: $Log" -ForegroundColor Yellow
      exit $p.ExitCode
  }
}
finally {
  Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}

if (-not $Background) {
    Write-Host "=== VELOS 마스터 스케줄러 완료 ===" -ForegroundColor Green
}
