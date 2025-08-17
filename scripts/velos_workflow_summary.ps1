# VELOS 워크플로우 실행 결과 요약 스크립트
# 실행 후 결과를 정리하고 다음 단계를 안내

param(
    [string]$WorkflowType = "ultimate",
    [switch]$ShowDetails,
    [switch]$CreateReport
)

$ErrorActionPreference = "Stop"

Write-Host "📊 VELOS 워크플로우 실행 결과 요약" -ForegroundColor Green
Write-Host "=" * 50

# 실행 가능한 워크플로우 목록
$workflows = @{
    "python" = @{
        "name" = "Python 완전 통합 워크플로우"
        "script" = "scripts\velos_ultimate_workflow.py"
        "description" = "Python으로 실행하는 완전 통합 워크플로우"
    }
    "powershell" = @{
        "name" = "PowerShell 완전 통합 워크플로우"
        "script" = "scripts\velos_ultimate_workflow.ps1"
        "description" = "PowerShell로 실행하는 완전 통합 워크플로우"
    }
    "individual" = @{
        "name" = "개별 스크립트 실행"
        "script" = "scripts\dispatch_all.ps1"
        "description" = "각 채널별 개별 스크립트 실행"
    }
}

# 워크플로우 선택
if ($WorkflowType -eq "list") {
    Write-Host "`n📋 사용 가능한 워크플로우:" -ForegroundColor Cyan
    foreach ($key in $workflows.Keys) {
        $wf = $workflows[$key]
        Write-Host "   $key`: $($wf.name)" -ForegroundColor Yellow
        Write-Host "      $($wf.description)" -ForegroundColor Gray
        Write-Host "      실행: $($wf.script)" -ForegroundColor Gray
    }
    return
}

# 선택된 워크플로우 정보
if ($workflows.ContainsKey($WorkflowType)) {
    $selectedWorkflow = $workflows[$WorkflowType]
    Write-Host "`n🎯 선택된 워크플로우: $($selectedWorkflow.name)" -ForegroundColor Cyan
    Write-Host "   설명: $($selectedWorkflow.description)" -ForegroundColor Gray
    Write-Host "   스크립트: $($selectedWorkflow.script)" -ForegroundColor Gray
} else {
    Write-Host "❌ 알 수 없는 워크플로우 타입: $WorkflowType" -ForegroundColor Red
    Write-Host "사용 가능한 타입: $($workflows.Keys -join ', ')" -ForegroundColor Yellow
    return
}

# 실행 전 체크리스트
Write-Host "`n🔍 실행 전 체크리스트:" -ForegroundColor Cyan
$checks = @(
    @{ "name" = "Python 가상환경"; "check" = { Test-Path "C:\Users\User\venvs\velos\Scripts\python.exe" } },
    @{ "name" = "환경변수 파일"; "check" = { Test-Path "C:\giwanos\configs\.env" } },
    @{ "name" = "보고서 디렉토리"; "check" = { Test-Path "C:\giwanos\data\reports\auto" } },
    @{ "name" = "최신 보고서 파일"; "check" = {
        $autoDir = "C:\giwanos\data\reports\auto"
        $latestPdf = Get-ChildItem -Path $autoDir -Filter "velos_auto_report_*_ko.pdf" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        return $null -ne $latestPdf
    }}
)

foreach ($check in $checks) {
    $result = & $check.check
    $status = if ($result) { "✅" } else { "❌" }
    $color = if ($result) { "Green" } else { "Red" }
    Write-Host "   $status $($check.name)" -ForegroundColor $color
}

# 환경변수 상태 확인
Write-Host "`n🔧 환경변수 상태:" -ForegroundColor Cyan
$envVars = @(
    "NOTION_TOKEN", "NOTION_DATABASE_ID", "SLACK_WEBHOOK_URL",
    "SMTP_HOST", "SMTP_USER", "SMTP_PASS", "PUSHBULLET_TOKEN"
)

foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    $status = if ($value) { "✅" } else { "❌" }
    $color = if ($value) { "Green" } else { "Red" }
    Write-Host "   $status $var" -ForegroundColor $color
}

# 실행 명령어 안내
Write-Host "`n🚀 실행 명령어:" -ForegroundColor Cyan
if ($WorkflowType -eq "python") {
    Write-Host "   python $($selectedWorkflow.script)" -ForegroundColor Yellow
} elseif ($WorkflowType -eq "powershell") {
    Write-Host "   .\$($selectedWorkflow.script)" -ForegroundColor Yellow
} elseif ($WorkflowType -eq "individual") {
    Write-Host "   .\$($selectedWorkflow.script)" -ForegroundColor Yellow
}

# 개별 스크립트 실행 안내
if ($ShowDetails) {
    Write-Host "`n📝 개별 스크립트 실행:" -ForegroundColor Cyan
    $individualScripts = @(
        @{ "name" = "Notion DB 생성"; "script" = "scripts\notion_db_create.py" },
        @{ "name" = "Notion Page 생성"; "script" = "scripts\notion_page_create.py" },
        @{ "name" = "Slack 알림"; "script" = "scripts\slack_notify.py" },
        @{ "name" = "이메일 전송"; "script" = "scripts\email_send.py" },
        @{ "name" = "Pushbullet 알림"; "script" = "scripts\pushbullet_send.py" }
    )

    foreach ($script in $individualScripts) {
        Write-Host "   python $($script.script)  # $($script.name)" -ForegroundColor Gray
    }
}

# 보고서 생성
if ($CreateReport) {
    Write-Host "`n📋 워크플로우 실행 보고서 생성 중..." -ForegroundColor Cyan

    $reportContent = @"
# VELOS 워크플로우 실행 보고서

## 실행 정보
- 실행 시간: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- 워크플로우: $($selectedWorkflow.name)
- 스크립트: $($selectedWorkflow.script)

## 체크리스트 결과
$(
    foreach ($check in $checks) {
        $result = & $check.check
        $status = if ($result) { "✅" } else { "❌" }
        "- $status $($check.name)"
    }
)

## 환경변수 상태
$(
    foreach ($var in $envVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        $status = if ($value) { "✅" } else { "❌" }
        "- $status $var"
    }
)

## 실행 명령어
```powershell
$(
    if ($WorkflowType -eq "python") {
        "python $($selectedWorkflow.script)"
    } elseif ($WorkflowType -eq "powershell") {
        ".`\$($selectedWorkflow.script)"
    } elseif ($WorkflowType -eq "individual") {
        ".`\$($selectedWorkflow.script)"
    }
)
```

## 개별 스크립트
$(
    foreach ($script in $individualScripts) {
        "- python $($script.script)  # $($script.name)"
    }
)
"@

    $reportPath = "C:\giwanos\data\reports\velos_workflow_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
    $reportContent | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Host "   보고서 생성 완료: $reportPath" -ForegroundColor Green
}

Write-Host "`n✨ VELOS 워크플로우 준비 완료!" -ForegroundColor Green
Write-Host "위의 실행 명령어를 사용하여 워크플로우를 시작하세요." -ForegroundColor Yellow
