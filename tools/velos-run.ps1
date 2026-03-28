# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
[CmdletBinding()] param([switch]$Once,[switch]$NoGit)
$ErrorActionPreference = "Stop"

Import-Module (Join-Path (Get-Location) "tools\velos.common.psm1") -Force

$ROOT = Get-VelosRoot
Set-Location $ROOT
$logs = Join-Path $ROOT "data\logs"
$autofixLog = Join-Path $logs "autofix.log"
Ensure-Dirs -Paths @($logs)

$log = New-VelosLogger -Name "velos-run" -LogPath $autofixLog

if(-not $NoGit){
  try { git config core.autocrlf input | Out-Null; git status --porcelain | Out-Null }
  catch { $log.Warn("Git unavailable; continuing.") }
}

function Invoke-VelosOnce{
  $py="python"; $script=Join-Path $ROOT "scripts\run_giwanos_master_loop.py"
  $env:PYTHONPATH="$ROOT;$ROOT\modules"
  $log.Info("start")
  try{
    $out = & $py $script 2>&1
    $code=$LASTEXITCODE
    if($code -ne 0){
      $out | Out-File -FilePath (Join-Path $logs "last_run.stderr.txt") -Encoding UTF8
      $log.Error(("python exit={0}" -f $code))
      throw "Master loop returned non-zero $code"
    } else {
      $out | Out-File -FilePath (Join-Path $logs "last_run.stdout.txt") -Encoding UTF8
      $log.Info("success")
    }
  } catch {
    $log.Error($_.Exception.Message)
    throw
  } finally {
    & pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "tools\self_check.ps1") | Out-Null
  }
}

if($Once){ Invoke-VelosOnce; exit 0 }
while($true){ try{ Invoke-VelosOnce } catch { $log.Warn($_) }; Start-Sleep -Seconds 300 }

# auto: sync changes to remote
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File ".\scripts\git_auto_sync.ps1" -Message "auto-sync: after velos-run"


# === auto-generate: create timestamped report & index ===
$env:PYTHONPATH = "$ROOT;$ROOT\modules"
try {
  python ".\scripts\auto_generate_runner.py" | Out-Null
  Write-Host "[auto-generate] ok"
} catch {
  Write-Host "[auto-generate] skipped: $($_.Exception.Message)"
}


# === auto-generate: create timestamped report & index (hardened) ===
try {
  $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not $Python) { $Python = (Get-Command py -ErrorAction SilentlyContinue).Source }
  if (-not $Python) { throw "python not found in PATH" }

  Push-Location $ROOT
  $env:PYTHONPATH = "$ROOT;$ROOT\modules"
  $pinfo = New-Object System.Diagnostics.ProcessStartInfo
  $pinfo.FileName = $Python
  $pinfo.Arguments = ".\scripts\auto_generate_runner.py"
  $pinfo.WorkingDirectory = $ROOT
  $pinfo.UseShellExecute = $false
  $pinfo.RedirectStandardOutput = $true
  $p = [System.Diagnostics.Process]::Start($pinfo)
  $null = $p.WaitForExit(60*1000)
  if ($p.HasExited -and $p.ExitCode -eq 0) {
    Write-Host "[auto-generate] ok"
  } else {
    Write-Host "[auto-generate][WARN] exit=$($p.ExitCode)"
  }
} catch {
  Write-Host "[auto-generate][FAIL] $($_.Exception.Message)"
} finally {
  Pop-Location
}


# [postrun] report:
try {
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\tools\velos-postrun.ps1"
} catch { Write-Host "[postrun][WARN] " }
