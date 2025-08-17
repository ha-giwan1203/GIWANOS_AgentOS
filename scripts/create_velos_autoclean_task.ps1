# create_velos_autoclean_task.ps1
# VELOS 자동 정리 워처 태스크 생성 스크립트

$ErrorActionPreference = 'Stop'

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "관리자 권한이 필요합니다. PowerShell을 관리자 권한으로 실행해주세요." -ForegroundColor Red
    Write-Host "다음 명령을 관리자 권한으로 실행하세요:" -ForegroundColor Yellow
    Write-Host "schtasks /create /tn `"VELOS-AutoClean-Watcher`" /tr `"wscript.exe C:\giwanos\scripts\Start-AutoClean-Hidden.vbs`" /sc onstart /ru SYSTEM /rl HIGHEST /f" -ForegroundColor Cyan
    exit 1
}

# 태스크 생성
try {
    $taskName = "VELOS-AutoClean-Watcher"
    $taskCommand = "wscript.exe C:\giwanos\scripts\Start-AutoClean-Hidden.vbs"
    
    Write-Host "VELOS 자동 정리 워처 태스크를 생성합니다..." -ForegroundColor Green
    Write-Host "태스크 이름: $taskName" -ForegroundColor Yellow
    Write-Host "실행 명령: $taskCommand" -ForegroundColor Yellow
    Write-Host "스케줄: 시스템 시작 시 자동 실행" -ForegroundColor Yellow
    
    # 기존 태스크 삭제 (있다면)
    schtasks /delete /tn $taskName /f 2>$null
    
    # 새 태스크 생성 (시스템 시작 시 실행)
    $result = schtasks /create /tn $taskName /tr $taskCommand /sc onstart /ru SYSTEM /rl HIGHEST /f
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ VELOS 자동 정리 워처 태스크가 성공적으로 생성되었습니다!" -ForegroundColor Green
        
        # 태스크 정보 확인
        Write-Host "`n생성된 태스크 정보:" -ForegroundColor Cyan
        schtasks /query /tn $taskName /fo table
        
        Write-Host "`n태스크 삭제 명령:" -ForegroundColor Yellow
        Write-Host "schtasks /delete /tn `"$taskName`" /f" -ForegroundColor Cyan
        
        Write-Host "`n수동 실행 명령:" -ForegroundColor Yellow
        Write-Host "wscript.exe C:\giwanos\scripts\Start-AutoClean-Hidden.vbs" -ForegroundColor Cyan
    } else {
        Write-Host "❌ 태스크 생성에 실패했습니다." -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ 오류가 발생했습니다: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
