# [ACTIVE] VELOS 통합 모니터링 시스템 - 통합 모니터링 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

param(
    [switch]$FixHidden,
    [switch]$CheckStats,
    [switch]$CheckTasks,
    [switch]$CheckIntegrity,
    [switch]$All
)

$ErrorActionPreference='Stop'
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT='C:\giwanos' }
$SETT = $env:VELOS_SETTINGS; if(-not $SETT){ $SETT = Join-Path $ROOT 'configs\settings.yaml' }

Write-Host "=== VELOS 통합 모니터링 시스템 ===" -ForegroundColor Yellow
Write-Host "[env] ROOT=$ROOT" -ForegroundColor Cyan
Write-Host "[env] SETTINGS=$SETT" -ForegroundColor Cyan

# 모든 체크를 실행하거나 개별 체크 실행
if ($All) {
    $CheckStats = $true
    $CheckTasks = $true
    $CheckIntegrity = $true
}

# 1) 핵심 경로 존재 확인
Write-Host "`n[1] 핵심 경로 확인..." -ForegroundColor Green
$must = @(
  'configs','data\memory','data\logs','data\snapshots',
  'interface','modules\core','scripts','tools','vector_cache'
) | % { Join-Path $ROOT $_ }

$ok=$true
foreach($p in $must){ 
    if(-not (Test-Path $p)){ 
        Write-Host "[MISS] $p" -ForegroundColor Red
        $ok=$false 
    } else { 
        Write-Host "[OK] $p" -ForegroundColor Green
    } 
}
if(-not $ok){ 
    Write-Host "❌ 필수 경로 누락" -ForegroundColor Red
    exit 1
}

# 2) 파이썬 구문검사
Write-Host "`n[2] Python 구문 검사..." -ForegroundColor Green
Push-Location $ROOT
$pyFiles = Get-ChildItem -Recurse -Filter *.py
$syntaxOk = $true
foreach($file in $pyFiles){
  try {
    python -m py_compile $file.FullName 2>$null
    Write-Host "[OK] $($file.Name)" -ForegroundColor Green
  } catch {
    Write-Host "[WARN] $($file.Name) - 구문 오류 가능성" -ForegroundColor Yellow
    $syntaxOk = $false
  }
}
if($syntaxOk){
  Write-Host "[OK] Python 구문 검사 통과" -ForegroundColor Green
} else {
  Write-Host "[WARN] 일부 Python 파일에 구문 오류 가능성" -ForegroundColor Yellow
}

# 3) 세션/메모리 selftest
Write-Host "`n[3] 세션/메모리 selftest..." -ForegroundColor Green
try {
    python -m modules.core.session_store --selftest
    Write-Host "[OK] session_store selftest 통과" -ForegroundColor Green
} catch {
    Write-Host "[WARN] session_store selftest 실패" -ForegroundColor Yellow
}

# 4) 통계 확인 (선택적)
if ($CheckStats) {
    Write-Host "`n[4] 시스템 통계 확인..." -ForegroundColor Green
    try {
        python scripts/check_velos_stats.py
        Write-Host "[OK] 통계 확인 완료" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] 통계 확인 실패" -ForegroundColor Yellow
    }
}

# 5) 태스크 확인 (선택적)
if ($CheckTasks) {
    Write-Host "`n[5] 스케줄 태스크 확인..." -ForegroundColor Green
    $names = @("VELOS Bridge Flush","VELOS Session Merge")
    foreach($n in $names){
        $xml = schtasks /query /tn $n /xml 2>$null
        if($xml){
            $normalizedXml = $xml -replace '\s+', ' '
            $hasWindowStyleHidden = $normalizedXml -match '-WindowStyle Hidden'
            if(-not $hasWindowStyleHidden){
                Write-Host "[WARN] $n 창 숨김 아님" -ForegroundColor Yellow
                if($FixHidden){
                    Write-Host "[FIX] $n 재생성" -ForegroundColor Cyan
                    schtasks /delete /tn $n /f 2>$null
                    if($n -eq "VELOS Session Merge"){
                        schtasks /create /tn $n /sc minute /mo 10 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\giwanos\velos_session_merge.bat" /f
                    } else {
                        schtasks /create /tn $n /sc minute /mo 1 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\giwanos\scripts\start_velos_bridge.ps1" /f
                    }
                    Write-Host "[OK] $n 창 숨김으로 재설정" -ForegroundColor Green
                }
            } else {
                Write-Host "[OK] $n Hidden" -ForegroundColor Green
            }
        } else {
            Write-Host "[INFO] $n 없음" -ForegroundColor Gray
        }
    }
}

# 6) 시스템 무결성 확인 (선택적)
if ($CheckIntegrity) {
    Write-Host "`n[6] 시스템 무결성 확인..." -ForegroundColor Green
    try {
        python scripts/system_integrity_check.py
        Write-Host "[OK] 시스템 무결성 확인 완료" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] 시스템 무결성 확인 실패" -ForegroundColor Yellow
    }
}

# 7) 대시보드 임포트 체크
Write-Host "`n[7] 대시보드 임포트 체크..." -ForegroundColor Green
$pythonCode = @"
import os,sys
root=os.environ.get('VELOS_ROOT','C:/giwanos')
sys.path.append(root)
mods=['interface.velos_dashboard','interface.status_dashboard']
ok=True
for m in mods:
  try:
    __import__(m); print('[OK] import', m)
  except Exception as e:
    ok=False; print('[ERR]', m, e)
raise SystemExit(0 if ok else 1)
"@
try {
    python -c $pythonCode
    Write-Host "[OK] 대시보드 임포트 체크 통과" -ForegroundColor Green
} catch {
    Write-Host "[WARN] 대시보드 임포트 체크 실패" -ForegroundColor Yellow
}

Pop-Location

Write-Host "`n=== VELOS 통합 모니터링 완료 ===" -ForegroundColor Green
Write-Host "사용법: .\scripts\velos_integrated_monitor.ps1 -All" -ForegroundColor Cyan

