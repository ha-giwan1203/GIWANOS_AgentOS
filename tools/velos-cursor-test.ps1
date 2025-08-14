$ErrorActionPreference="Stop"
$root="C:\giwanos"
$failFlag=Join-Path $root "data\logs\force_fail.flag"

function Show($p){
    if(Test-Path $p){
        Write-Host "`n=== $p ==="
        Get-Content $p -Raw
    } else {
        Write-Host "`n=== $p (MISSING) ===" -ForegroundColor Yellow
    }
}

# 1) 초기 상태
Show (Join-Path $root "data\logs\loop_state_tracker.json")
Show (Join-Path $root "data\memory\memory_cursor.json")
Show (Join-Path $root "data\reports\report_cursor.json")

# 2) 정상 실행
pwsh -File (Join-Path $root "tools\velos-run.ps1") -Once

# 3) 실패 주입 → 실패 확인
Set-Content -Path $failFlag -Value "boom" -Encoding UTF8
try {
    pwsh -File (Join-Path $root "tools\velos-run.ps1") -Once
} catch {
    Write-Host "[test] expected failure captured" -ForegroundColor Yellow
}
Remove-Item $failFlag -Force -ErrorAction SilentlyContinue

# 4) 재개 실행
pwsh -File (Join-Path $root "tools\velos-run.ps1") -Once

# 5) 상태 출력
Show (Join-Path $root "data\logs\loop_state_tracker.json")
Get-ChildItem (Join-Path $root "data\reports\auto") | Sort-Object LastWriteTime -Descending | Select-Object -First 3
Get-Content (Join-Path $root "data\reports\auto\self_check_summary.txt") -TotalCount 30