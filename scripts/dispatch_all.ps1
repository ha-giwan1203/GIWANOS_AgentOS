# [ACTIVE] VELOS 전체 디스패치 시스템 - 전체 디스패치 스크립트
# scripts/dispatch_all.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 VELOS 전체 디스패치 시작" -ForegroundColor Green
Write-Host "=" * 50

$results = @{}

# Slack 디스패치
Write-Host "`n📱 Slack 디스패치 중..." -ForegroundColor Cyan
try {
    python scripts/dispatch_slack.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Slack 성공" -ForegroundColor Green
        $results["slack"] = "success"
    } else {
        Write-Host "❌ Slack 실패" -ForegroundColor Red
        $results["slack"] = "failed"
    }
} catch {
    Write-Host "❌ Slack 오류: $_" -ForegroundColor Red
    $results["slack"] = "error"
}

# Email 디스패치
Write-Host "`n📧 Email 디스패치 중..." -ForegroundColor Cyan
try {
    python scripts/dispatch_email.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Email 성공" -ForegroundColor Green
        $results["email"] = "success"
    } else {
        Write-Host "❌ Email 실패" -ForegroundColor Red
        $results["email"] = "failed"
    }
} catch {
    Write-Host "❌ Email 오류: $_" -ForegroundColor Red
    $results["email"] = "error"
}

# Notion 디스패치
Write-Host "`n📝 Notion 디스패치 중..." -ForegroundColor Cyan
try {
    python scripts/dispatch_notion.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Notion 성공" -ForegroundColor Green
        $results["notion"] = "success"
    } else {
        Write-Host "❌ Notion 실패" -ForegroundColor Red
        $results["notion"] = "failed"
    }
} catch {
    Write-Host "❌ Notion 오류: $_" -ForegroundColor Red
    $results["notion"] = "error"
}

# Pushbullet 디스패치
Write-Host "`n📱 Pushbullet 디스패치 중..." -ForegroundColor Cyan
try {
    python scripts/dispatch_push.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Pushbullet 성공" -ForegroundColor Green
        $results["pushbullet"] = "success"
    } else {
        Write-Host "❌ Pushbullet 실패" -ForegroundColor Red
        $results["pushbullet"] = "failed"
    }
} catch {
    Write-Host "❌ Pushbullet 오류: $_" -ForegroundColor Red
    $results["pushbullet"] = "error"
}

# 결과 요약
Write-Host "`n📊 디스패치 결과 요약" -ForegroundColor Yellow
Write-Host "=" * 30

$success_count = 0
foreach ($channel in $results.Keys) {
    $status = $results[$channel]
    if ($status -eq "success") {
        Write-Host "✅ $channel" -ForegroundColor Green
        $success_count++
    } elseif ($status -eq "failed") {
        Write-Host "❌ $channel" -ForegroundColor Red
    } else {
        Write-Host "⚠️  $channel" -ForegroundColor Yellow
    }
}

Write-Host "`n🎯 성공률: $success_count/4 ($([math]::Round($success_count/4*100, 1))%)" -ForegroundColor $(if ($success_count -eq 4) { "Green" } elseif ($success_count -ge 2) { "Yellow" } else { "Red" })

# 종료 코드
if ($success_count -eq 4) {
    Write-Host "`n🎉 모든 채널 성공!" -ForegroundColor Green
    exit 0
} elseif ($success_count -ge 2) {
    Write-Host "`n⚠️  부분적 성공" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "`n💥 대부분 실패" -ForegroundColor Red
    exit 2
}



