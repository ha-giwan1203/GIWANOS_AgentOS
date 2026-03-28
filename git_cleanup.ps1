$ErrorActionPreference = "Stop"
Set-Location "$env:USERPROFILE\Desktop"

Write-Host "=== [1/7] Clone ===" -ForegroundColor Cyan
if (Test-Path "GIWANOS_clean") { Remove-Item -Recurse -Force "GIWANOS_clean" }
git clone https://github.com/ha-giwan1203/GIWANOS_AgentOS.git GIWANOS_clean
Set-Location "GIWANOS_clean"

Write-Host "=== [2/7] Untrack large dirs ===" -ForegroundColor Cyan
git rm -r --cached data/
git rm -r --cached fonts/
git rm -r --cached artifacts/
git rm -r --cached backup/
git rm -r --cached archive/

Write-Host "=== [3/7] Add .keep ===" -ForegroundColor Cyan
New-Item -ItemType File -Path "data/.keep" -Force | Out-Null
New-Item -ItemType File -Path "fonts/.keep" -Force | Out-Null
New-Item -ItemType File -Path "artifacts/.keep" -Force | Out-Null
git add -f data/.keep fonts/.keep artifacts/.keep

Write-Host "=== [4/7] Relocate root files ===" -ForegroundColor Cyan
git mv memory_loader.py scripts/
git mv phase2_analysis.py scripts/
git mv phase2_batch_update.py scripts/
git mv validate_phase1_fixes.py scripts/
git mv memory_health_check_all.py scripts/
git mv COMPREHENSIVE_SCHEDULER_RECHECK_GUIDE.md docs/
git mv VELOS_MASTER_SCHEDULER_GUIDE.md docs/
git mv VELOS_SCHEDULER_OPTIMIZATION_GUIDE.md docs/
git mv VELOS_Bridge_AutoStart_Fixed.xml configs/
git mv VELOS_Bridge_AutoStart_Improved.xml configs/
git mv VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml configs/
git mv WINDOWS_VERIFICATION_SCRIPT.ps1 scripts/

Write-Host "=== [5/7] Update .gitignore ===" -ForegroundColor Cyan
$content = Get-Content .gitignore -Raw -Encoding UTF8
$old = "artifacts/`nfonts/**`n!fonts/.keep`n`ndata/`n!data/.keep`n!data/README.md"
$new = "artifacts/`n!artifacts/.keep`n`nfonts/`n!fonts/.keep`n`ndata/`n!data/.keep`n`nbackup/`narchive/"
$content = $content.Replace($old, $new)
[System.IO.File]::WriteAllText("$(Get-Location)\.gitignore", $content, [System.Text.Encoding]::UTF8)

Write-Host "=== [6/7] Commit ===" -ForegroundColor Cyan
git add -A
git commit -m "refactor: cleanup repo - remove 1500+ unneeded tracked files, reorganize root"

Write-Host "=== [7/7] Push ===" -ForegroundColor Cyan
git push origin main

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
(git ls-files | Measure-Object).Count
