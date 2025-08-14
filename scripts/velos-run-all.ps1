[CmdletBinding()]
param(
  [switch]$NoOpen,     # postrun에서 Cursor 열기 생략
  [switch]$NoPush,     # postrun에서 git push 생략
  [switch]$VerbosePy   # 파이썬 루프를 --verbose로
)

$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if (-not $ROOT) { $ROOT = "C:\giwanos" }
$ROOT = [IO.Path]::GetFullPath($ROOT)
Set-Location $ROOT

# 환경 변수 로드
$envFile = Join-Path $ROOT "configs\.env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
      $key = $matches[1].Trim()
      $value = $matches[2].Trim()
      Set-Item -Path "env:$key" -Value $value
    }
  }
}

function Info($m) { Write-Host "[run-all] $m" }
function Warn($m) { Write-Host "[run-all][WARN] $m" -ForegroundColor Yellow }

# 0) venv 활성화(있으면)
$venv = Join-Path $ROOT "venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
  . $venv
  Info "venv activated: $venv"
}
else {
  Warn "venv not found. system python 사용"
}

# 1) 마스터 루프 실행(파이썬 or 기존 ps1 중 가용한 쪽)
$py = (Get-Command python -ErrorAction SilentlyContinue)
$loopPy = Join-Path $ROOT "scripts\run_giwanos_master_loop.py"
$loopPs = Join-Path $ROOT "tools\velos-run.ps1"

if ($py -and (Test-Path $loopPy)) {
  $args = @()
  if ($VerbosePy) { $args += "--verbose" }
  Info "run python loop..."
  
  # VENV_PATH 환경 변수를 사용하여 Python 경로 결정
  $venvPython = Join-Path $ROOT ".venv_link\Scripts\python.exe"
  if (Test-Path $venvPython) {
    Info "using venv python: $venvPython"
  }
  else {
    Write-Warning "[run-all] venv python not found -> system python"
    $venvPython = "python"
  }
  
  & $venvPython $loopPy @args
  $code = $LASTEXITCODE
}
elseif (Test-Path $loopPs) {
  Info "run velos-run.ps1 -Once..."
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $loopPs -Once
  $code = $LASTEXITCODE
}
else {
  throw "마스터 루프 엔트리 없음: $loopPy / $loopPs"
}

if ($code -ne 0) {
  Warn ("master loop exited with code {0}" -f $code)
}

# 2) postrun 호출(리포트 찾기 + git push + Cursor 열기)
$post = Join-Path $ROOT "tools\velos-postrun.ps1"
if (-not (Test-Path $post)) { throw "postrun 스크립트 없음: $post" }

$prArgs = @()
if ($NoOpen) { $prArgs += "-NoOpen" }
if ($NoPush) { $prArgs += "-NoPush" }

Info "postrun..."
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $post @prArgs
Info "done."

