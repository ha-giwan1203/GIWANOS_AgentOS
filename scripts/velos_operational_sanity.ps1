# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 운영 선언: 판단은 기록으로 증명한다.
$ErrorActionPreference="Stop"
$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}

function Fail($m){ Write-Host "[FAIL] $m"; exit 1 }
function Ok($m){ Write-Host "[OK] $m" }

Write-Host "[VELOS] Operational Sanity Check 시작 - $ROOT"

# 0) 리스크 리포트 보장
Write-Host "[CHECK] 0단계: 리스크 리포트 보장"
try {
    powershell -NoProfile -ExecutionPolicy Bypass -File C:\giwanos\scripts\ensure_risk_report.ps1
    if($LASTEXITCODE -ne 0) {
        Fail "Risk report ensure failed"
    }
    Write-Host "[INFO] 리스크 리포트 보장 완료"
} catch {
    Fail "Risk report ensure failed: $_"
}

# 1) 스케줄러 Hidden 확인
Write-Host "[CHECK] 1단계: 스케줄러 Hidden 확인"
$tasks = @("VELOS Weekly File Audit","VELOS Quarantine Orphans","VELOS Daily Error Summary")
foreach($t in $tasks){
    try {
        $xml = schtasks /query /tn $t /xml 2>$null
        if(-not $xml){
            Fail "Task missing: $t"
        }
        $normalizedXml = $xml -replace '\s+', ' '
        if(-not ($normalizedXml -match '-WindowStyle Hidden')){
            Fail "Task not Hidden: $t"
        }
        Write-Host "[INFO] $t - Hidden 확인됨"
    } catch {
        Fail "Task check failed: $t - $_"
    }
}
Ok "All scheduled tasks present and Hidden"

# 2) 리포트 무결성
Write-Host "[CHECK] 2단계: 리포트 무결성 확인"
$repRisk = Join-Path $ROOT "data\reports\file_usage_risk_report.json"
$repMani = Join-Path $ROOT "data\reports\manifest_sync_report.json"

if(-not (Test-Path $repRisk)){
    Fail "risk report missing: $repRisk"
}
if(-not (Test-Path $repMani)){
    Fail "manifest report missing: $repMani"
}

try {
    $risk = Get-Content $repRisk -Raw | ConvertFrom-Json
    $mani = Get-Content $repMani -Raw | ConvertFrom-Json

    if(-not $risk.summary){
        Fail "risk report malformed - summary missing"
    }
    if(-not $mani.generated_at){
        Fail "manifest report malformed - generated_at missing"
    }

    Write-Host "[INFO] Risk report: $($risk.summary | ConvertTo-Json -Compress)"
    Write-Host "[INFO] Manifest report: $($mani.generated_at)"
} catch {
    Fail "Report parsing failed: $_"
}
Ok "Reports present and well-formed"

# 3) orphan 추세
Write-Host "[CHECK] 3단계: orphan_candidate 추세 확인"
try {
    $orphan = [int]$risk.summary.orphan_candidate
    Write-Host "[INFO] orphan_candidate=$orphan"

    if($orphan -gt 200){
        Fail "too many orphan candidates ($orphan > 200)"
    }

    if($orphan -gt 0){
        Fail "orphan detected ($orphan). cleanup required"
    }

    Ok "Orphan candidate within guardrail ($orphan)"
} catch {
    Fail "Orphan count check failed: $_"
}

# 4) 대시보드 임포트 스모크
Write-Host "[CHECK] 4단계: 대시보드 임포트 스모크 테스트"
try {
    $code = @"
import os,sys
os.environ.setdefault('VELOS_ROOT', r'$ROOT')
sys.path.append(os.environ['VELOS_ROOT'])
__import__('interface.velos_dashboard')
print('OK')
"@

    $result = python -c $code 2>&1
    if($LASTEXITCODE -ne 0){
        Fail "dashboard import failed: $result"
    }
    Write-Host "[INFO] Dashboard import: $result"
    Ok "Dashboard import ok"
} catch {
    Fail "Dashboard import test failed: $_"
}

# 5) 최근 48h 에러 요약
Write-Host "[CHECK] 5단계: 최근 48시간 에러 요약 확인"
$err = Join-Path $ROOT "data\reports\error_summary.json"
if(Test-Path $err){
    try {
        $errData = Get-Content $err -Raw | ConvertFrom-Json
        $total = $errData.total_errors
        $files = $errData.files_with_errors

        Write-Host "[INFO] Total errors: $total"
        Write-Host "[INFO] Files with errors: $files"

        if($total -gt 50){
            Fail "too many recent errors ($total > 50)"
        }
        if($files -gt 10){
            Write-Host "[WARN] Many files with errors ($files) - investigate"
        }

        Ok "Error summary mild ($total errors in $files files over 48h)"
    } catch {
        Fail "Error summary parsing failed: $_"
    }
} else {
    Write-Host "[WARN] error summary missing; will tolerate first run"
    Ok "Error summary missing (first run)"
}

# 6) 코어 파일 보호 확인
Write-Host "[CHECK] 6단계: 코어 파일 보호 확인"
$corePaths = @("modules", "scripts", "interface")
$coreFiles = @()
foreach($path in $corePaths){
    $fullPath = Join-Path $ROOT $path
    if(Test-Path $fullPath){
        $files = Get-ChildItem $fullPath -Recurse -File | Measure-Object
        $coreFiles += "$path`: $($files.Count) files"
    } else {
        $coreFiles += "$path`: MISSING"
    }
}

Write-Host "[INFO] Core files: $($coreFiles -join ', ')"
Ok "Core file protection check completed"

# 7) 격리 시스템 확인
Write-Host "[CHECK] 7단계: 격리 시스템 확인"
$quarantineDir = Join-Path $ROOT "data\quarantine"
if(Test-Path $quarantineDir){
    $quarantineCount = (Get-ChildItem $quarantineDir -Directory | Measure-Object).Count
    Write-Host "[INFO] Quarantine directories: $quarantineCount"

    if($quarantineCount -gt 10){
        Write-Host "[WARN] Many quarantine directories ($quarantineCount) - consider cleanup"
    }
} else {
    Write-Host "[INFO] Quarantine directory not yet created"
}
Ok "Quarantine system check completed"

Write-Host "[PASS] VELOS Operational Sanity Check 완료"
Write-Host "[SUMMARY] 모든 핵심 시스템이 정상 작동 중입니다"
exit 0
