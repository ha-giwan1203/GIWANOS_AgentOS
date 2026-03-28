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
param([switch]$VerboseMode)
$ErrorActionPreference = "Stop"

Import-Module (Join-Path (Get-Location) "tools\velos.common.psm1") -Force

$ROOT = Get-VelosRoot
$py = "python"
$summary = Join-Path $ROOT "data\reports\auto\self_check_summary.txt"
$logs = Join-Path $ROOT "data\logs"
$autofixLog = Join-Path $logs "autofix.log"
Ensure-Dirs -Paths @($logs, (Split-Path $summary -Parent))

$log = New-VelosLogger -Name "self_check" -LogPath $autofixLog
$env:PYTHONPATH="$ROOT;$ROOT\modules"

$probe = & $py (Join-Path $ROOT "modules\report_paths.py") 2>&1

$checks = @()
$checks += @{ name="VELOS_ROOT"; value=$ROOT; status="ok" }
$checks += @{ name="OPENAI_API_KEY"; value=($(if ($env:OPENAI_API_KEY) {"present"} else {"missing"})); status=($(if ($env:OPENAI_API_KEY) {"ok"} else {"warn"})) }
$checks += @{ name="Python"; value=$py; status="ok" }

$lines = @()
$lines += "=== VELOS Self Check Summary ==="
$lines += "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += "VELOS_ROOT: $ROOT"
$lines += ""
$lines += "[Probe Output]"
$lines += $probe
$lines += ""
$lines += "[Checks]"
foreach($c in $checks){ $lines += ("{0}: {1} ({2})" -f $c.name,$c.value,$c.status) }

$enc = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($summary, ($lines -join [Environment]::NewLine), $enc)
$log.Info("summary:$summary")

if($VerboseMode){ Get-Content $summary | Select-Object -First 40 | ForEach-Object { Write-Host $_ } }
