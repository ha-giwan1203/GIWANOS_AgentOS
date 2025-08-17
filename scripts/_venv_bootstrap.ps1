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
