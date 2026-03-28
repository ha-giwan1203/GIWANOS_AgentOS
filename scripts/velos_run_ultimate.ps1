# [ACTIVE] VELOS 최종 워크플로우 실행 시스템 - 최종 완전 통합 워크플로우 실행 스크립트
# VELOS 최종 완전 통합 워크플로우 실행 스크립트
# 사용자가 제공한 명령어를 기반으로 작업 스케줄러 등록 및 실행

$ErrorActionPreference = "Stop"

Write-Host "🚀 VELOS 최종 완전 통합 워크플로우 실행" -ForegroundColor Green
Write-Host "=" * 50

# 작업 스케줄러 등록 명령어
Write-Host "`n📋 작업 스케줄러 등록 명령어:" -ForegroundColor Cyan
Write-Host "다음 명령어를 관리자 권한으로 실행된 PowerShell에서 실행하세요:" -ForegroundColor Yellow

$taskName = "VELOS_Ultimate"
$script = "C:\giwanos\scripts\velos_ultimate_workflow.ps1"
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoLogo -NoProfile -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 09:00
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

$commands = @"

# VELOS 작업 스케줄러 등록 명령어
`$taskName = "$taskName"
`$script = "$script"
`$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoLogo -NoProfile -File `"`$script`""
`$trigger = New-ScheduledTaskTrigger -Daily -At 09:00
`$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName `$taskName -Action `$action -Trigger `$trigger -Settings `$settings -Description "VELOS daily dispatch"

"@

Write-Host $commands -ForegroundColor Gray

# 수동 실행 명령어
Write-Host "`n🔧 수동 실행 명령어:" -ForegroundColor Cyan
Write-Host "   PowerShell 워크플로우: .\scripts\velos_ultimate_workflow.ps1" -ForegroundColor Yellow
Write-Host "   Python 워크플로우: python scripts\velos_ultimate_workflow.py" -ForegroundColor Yellow
Write-Host "   개별 스크립트: .\scripts\dispatch_all.ps1" -ForegroundColor Yellow

# 작업 관리 명령어
Write-Host "`n🔧 작업 관리 명령어:" -ForegroundColor Cyan
Write-Host "   📋 작업 목록: Get-ScheduledTask -TaskName '*VELOS*'" -ForegroundColor Gray
Write-Host "   ▶️  작업 시작: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "   ⏸️  작업 중지: Stop-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "   🔄 작업 활성화: Enable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "   🚫 작업 비활성화: Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host "   🗑️  작업 제거: Unregister-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray

# 즉시 실행 옵션
Write-Host "`n⚡ 즉시 실행 옵션:" -ForegroundColor Cyan
Write-Host "   지금 바로 워크플로우를 실행하려면 다음 명령어를 사용하세요:" -ForegroundColor Yellow
Write-Host "   .\scripts\velos_ultimate_workflow.ps1" -ForegroundColor Green

Write-Host "`n✨ VELOS 최종 완전 통합 워크플로우 준비 완료!" -ForegroundColor Green
Write-Host "위의 명령어를 사용하여 작업 스케줄러에 등록하거나 즉시 실행하세요." -ForegroundColor Yellow



