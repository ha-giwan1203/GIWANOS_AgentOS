# VELOS Windows 작업 스케줄러 등록 스크립트
# VELOS 최종 완전 통합 워크플로우를 자동으로 실행하도록 스케줄링

param(
    [string]$TaskName = "VELOS_Ultimate",
    [string]$ScriptPath = "C:\giwanos\scripts\velos_ultimate_workflow.ps1",
    [string]$Schedule = "Daily",  # Daily, Weekly, Monthly
    [string]$Time = "09:00",
    [string]$Description = "VELOS daily dispatch - 완전 통합 워크플로우 자동 실행",
    [switch]$Remove,
    [switch]$List,
    [switch]$Test
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 VELOS Windows 작업 스케줄러 설정" -ForegroundColor Green
Write-Host "=" * 50

# 관리자 권한 확인
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "❌ 관리자 권한이 필요합니다!" -ForegroundColor Red
    Write-Host "   PowerShell을 관리자 권한으로 실행해주세요." -ForegroundColor Yellow
    exit 1
}

# 기존 작업 목록 확인
if ($List) {
    Write-Host "`n📋 기존 VELOS 관련 작업 목록:" -ForegroundColor Cyan
    $existingTasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*VELOS*" }

    if ($existingTasks) {
        foreach ($task in $existingTasks) {
            Write-Host "   📋 $($task.TaskName)" -ForegroundColor Yellow
            Write-Host "      상태: $($task.State)" -ForegroundColor Gray
            Write-Host "      설명: $($task.Description)" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "   📭 VELOS 관련 작업이 없습니다." -ForegroundColor Gray
    }
    return
}

# 작업 제거
if ($Remove) {
    Write-Host "`n🗑️  작업 제거 중..." -ForegroundColor Cyan

    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "✅ 작업 '$TaskName' 제거 완료" -ForegroundColor Green
        } else {
            Write-Host "⚠️  작업 '$TaskName'을 찾을 수 없습니다." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ 작업 제거 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
    return
}

# 스크립트 파일 존재 확인
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ 스크립트 파일을 찾을 수 없습니다: $ScriptPath" -ForegroundColor Red
    Write-Host "   스크립트 경로를 확인해주세요." -ForegroundColor Yellow
    exit 1
}

Write-Host "📄 스크립트 경로: $ScriptPath" -ForegroundColor Cyan
Write-Host "📋 작업 이름: $TaskName" -ForegroundColor Cyan
Write-Host "⏰ 실행 시간: $Schedule $Time" -ForegroundColor Cyan

# 기존 작업 확인
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "`n⚠️  기존 작업이 존재합니다: $TaskName" -ForegroundColor Yellow
    Write-Host "   기존 작업을 제거하고 새로 생성합니다." -ForegroundColor Yellow

    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 기존 작업 제거 완료" -ForegroundColor Green
    } catch {
        Write-Host "❌ 기존 작업 제거 실패: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# 작업 액션 생성
Write-Host "`n🔧 작업 액션 생성 중..." -ForegroundColor Cyan
try {
    $action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    Write-Host "✅ 작업 액션 생성 완료" -ForegroundColor Green
} catch {
    Write-Host "❌ 작업 액션 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 작업 트리거 생성
Write-Host "🔧 작업 트리거 생성 중..." -ForegroundColor Cyan
try {
    switch ($Schedule.ToLower()) {
        "daily" {
            $trigger = New-ScheduledTaskTrigger -Daily -At $Time
        }
        "weekly" {
            $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $Time
        }
        "monthly" {
            $trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At $Time
        }
        default {
            Write-Host "❌ 지원하지 않는 스케줄: $Schedule" -ForegroundColor Red
            Write-Host "   지원: Daily, Weekly, Monthly" -ForegroundColor Yellow
            exit 1
        }
    }
    Write-Host "✅ 작업 트리거 생성 완료" -ForegroundColor Green
} catch {
    Write-Host "❌ 작업 트리거 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 작업 설정 생성
Write-Host "🔧 작업 설정 생성 중..." -ForegroundColor Cyan
try {
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    Write-Host "✅ 작업 설정 생성 완료" -ForegroundColor Green
} catch {
    Write-Host "❌ 작업 설정 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 작업 등록
Write-Host "🔧 작업 등록 중..." -ForegroundColor Cyan
try {
    $task = Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description $Description
    Write-Host "✅ 작업 등록 완료!" -ForegroundColor Green
} catch {
    Write-Host "❌ 작업 등록 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 작업 정보 출력
Write-Host "`n📋 등록된 작업 정보:" -ForegroundColor Cyan
Write-Host "   📋 작업 이름: $($task.TaskName)" -ForegroundColor Yellow
Write-Host "   📝 설명: $($task.Description)" -ForegroundColor Gray
Write-Host "   ⏰ 실행 시간: $Schedule $Time" -ForegroundColor Gray
Write-Host "   📄 스크립트: $ScriptPath" -ForegroundColor Gray
Write-Host "   🔄 상태: $($task.State)" -ForegroundColor Gray

# 작업 테스트
if ($Test) {
    Write-Host "`n🧪 작업 테스트 실행 중..." -ForegroundColor Cyan
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "✅ 작업 테스트 시작 완료" -ForegroundColor Green
        Write-Host "   작업이 백그라운드에서 실행 중입니다." -ForegroundColor Gray
    } catch {
        Write-Host "❌ 작업 테스트 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 관리 명령어 안내
Write-Host "`n🔧 작업 관리 명령어:" -ForegroundColor Cyan
Write-Host "   📋 작업 목록: Get-ScheduledTask -TaskName '*VELOS*'" -ForegroundColor Gray
Write-Host "   ▶️  작업 시작: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   ⏸️  작업 중지: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   🔄 작업 활성화: Enable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   🚫 작업 비활성화: Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   🗑️  작업 제거: Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray

Write-Host "`n✨ VELOS 작업 스케줄러 설정 완료!" -ForegroundColor Green
Write-Host "매일 $Time에 VELOS 최종 완전 통합 워크플로우가 자동으로 실행됩니다." -ForegroundColor Yellow
