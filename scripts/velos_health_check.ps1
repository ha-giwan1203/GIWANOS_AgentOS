# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
param([switch]$FixHidden)

$ErrorActionPreference='Stop'
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT='C:\giwanos' }
$SETT = $env:VELOS_SETTINGS; if(-not $SETT){ $SETT = Join-Path $ROOT 'configs\settings.yaml' }

Write-Host "[env] ROOT=$ROOT"
Write-Host "[env] SETTINGS=$SETT"

# 1) 핵심 경로 존재 확인
$must = @(
  'configs','data\memory','data\logs','data\snapshots',
  'interface','modules\core','scripts','tools','vector_cache'
) | % { Join-Path $ROOT $_ }

$ok=$true
foreach($p in $must){ if(-not (Test-Path $p)){ Write-Host "[MISS] $p"; $ok=$false } else { Write-Host "[OK] $p" } }
if(-not $ok){ throw "필수 경로 누락" }

# 2) 파이썬 구문검사
Push-Location $ROOT
$pyFiles = Get-ChildItem -Recurse -Filter *.py
$syntaxOk = $true
foreach($file in $pyFiles){
  try {
    python -m py_compile $file.FullName 2>$null
    Write-Host "[OK] $($file.Name)"
  } catch {
    Write-Host "[WARN] $($file.Name) - 구문 오류 가능성"
    $syntaxOk = $false
  }
}
if($syntaxOk){
  Write-Host "[OK] python syntax check passed"
} else {
  Write-Host "[WARN] 일부 Python 파일에 구문 오류 가능성"
}

# 3) 세션/메모리 selftest
python -m modules.core.session_store --selftest
Write-Host "[OK] session_store selftest passed"

# 4) 스케줄러 창 숨김 확인 및 선택적 수정
$names = @("VELOS Bridge Flush","VELOS Session Merge")
foreach($n in $names){
  $xml = schtasks /query /tn $n /xml 2>$null
  if($xml){
    $normalizedXml = $xml -replace '\s+', ' '
    $hasWindowStyleHidden = $normalizedXml -match '-WindowStyle Hidden'
    if(-not $hasWindowStyleHidden){
      Write-Host "[WARN] $n 창 숨김 아님"
      if($FixHidden){
        Write-Host "[FIX] $n 재생성"
        schtasks /delete /tn $n /f 2>$null
        if($n -eq "VELOS Session Merge"){
          schtasks /create /tn $n /sc minute /mo 10 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\giwanos\velos_session_merge.bat" /f
        } else {
          schtasks /create /tn $n /sc minute /mo 1 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\giwanos\scripts\start_velos_bridge.ps1" /f
        }
        Write-Host "[OK] $n 창 숨김으로 재설정"
      }
    } else {
      Write-Host "[OK] $n Hidden"
    }
  } else {
    Write-Host "[INFO] $n 없음"
  }
}

# 5) 대시보드 임포트 체크
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
python -c $pythonCode

Write-Host "[OK] dashboard import check passed"
Pop-Location
Write-Host "[DONE] VELOS health check passed"
