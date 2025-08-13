# _venv_bootstrap.ps1 — venv 활성화 + .env 로드 (PowerShell 전용)
/* no-op for editors that highlight C-style comments */

param(
  [string] $VenvPath    = "C:/Users/User/venvs/velos",
  [string] $EnvFilePath = "C:/Users/User/venvs/velos/.env"
)

$ErrorActionPreference = "Stop"

function Use-Venv {
  param([string]$Path)
  $activate = "$Path/Scripts/Activate.ps1"
  if (!(Test-Path $activate)) { throw "venv not found: $Path" }
  . $activate
}

function Import-Dotenv {
  param([string]$File)
  if (!(Test-Path $File)) { Write-Host "[warn] .env not found: $File"; return }
  Get-Content -Raw -Encoding UTF8 $File `
  | ForEach-Object {
      $_ -split "`n"
    } `
  | ForEach-Object {
      $line = $_.Trim()
      if (!$line) { return }
      if ($line.StartsWith("#")) { return }
      $kv = $line -split "=", 2
      if ($kv.Count -lt 2) { return }
      $k = $kv[0].Trim()
      $v = $kv[1].Trim().Trim('"').Trim("'")
      $env:$k = $v
    }
  Write-Host "[ok] .env loaded: $File"
}

# 1) venv 활성화
Use-Venv -Path $VenvPath

# 2) .env 로드
Import-Dotenv -File $EnvFilePath

# 3) 간단 점검
$py = "$VenvPath/Scripts/python.exe"
Write-Host "[ok] PYTHON => $py"
& $py -c "import sys,os; print('python', sys.version.split()[0]); print('SLACK_BOT_TOKEN set =', bool(os.getenv('SLACK_BOT_TOKEN')))"
