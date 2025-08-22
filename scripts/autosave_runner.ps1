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
[CmdletBinding()] param([int]$DebounceMs=1500)
$ErrorActionPreference="Stop"
$ROOT = "C:\giwanos"
$LOCK = Join-Path $ROOT "data\logs\run.lock"
$LOG  = Join-Path $ROOT ("data\logs\autosave_runner_{0}.log" -f (Get-Date -Format yyyyMMdd))
$script:lastRun = 0

function Log($m){ "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"),$m | Out-File -FilePath $LOG -Append -Encoding UTF8 }

function KickRun([string]$reason,[string]$path){
  $now=[Environment]::TickCount64
  if ($now - $script:lastRun -lt $DebounceMs){ return }
  if (Test-Path $LOCK){ Log "skip(lock): $reason :: $path"; return }
  try {
    New-Item -ItemType File -Path $LOCK -Force | Out-Null
    Log "preflight... ($reason :: $path)"
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\preflight_quickcheck.ps1" 2>$null
    if ($LASTEXITCODE -ne 0){ Log "preflight FAIL ($reason)"; return }
    Log "run start"
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos-run-all.ps1" -NoOpen
    Log "run done"
  } catch {
    Log ("ERROR: {0}" -f $_.Exception.Message)
  } finally {
    Remove-Item $LOCK -Force -ErrorAction SilentlyContinue
    $script:lastRun = [Environment]::TickCount64
  }
}

# ===== Watcher =====
$watchRoots = @("$ROOT")
$filters    = @("*.py","*.ps1","*.json")

foreach($wr in $watchRoots){
  $fsw = New-Object IO.FileSystemWatcher $wr, "*.*"
  $fsw.IncludeSubdirectories = $true
  $fsw.EnableRaisingEvents  = $true
  $fsw.NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite, Size'

  Register-ObjectEvent $fsw Changed -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Changed :: $p";  KickRun "Changed" $p
  } | Out-Null
  Register-ObjectEvent $fsw Created -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Created :: $p";  KickRun "Created" $p
  } | Out-Null
  Register-ObjectEvent $fsw Renamed -Action {
    $p=$EventArgs.FullPath; if($filters -notcontains ("*"+[IO.Path]::GetExtension($p))){return}
    Log "event: Renamed :: $p";  KickRun "Renamed" $p
  } | Out-Null
}

"[{0}] watch start" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss") | Out-File -FilePath $LOG -Append -Encoding UTF8
# CPU 사용량 최적화: 400ms -> 2000ms (2초)로 증가
while($true){ Start-Sleep -Milliseconds 2000 }
