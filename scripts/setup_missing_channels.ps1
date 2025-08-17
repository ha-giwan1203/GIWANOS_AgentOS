# VELOS 누락된 채널 환경변수 설정 가이드
# 사용법: .\scripts\setup_missing_channels.ps1

Write-Host "🔧 VELOS 누락된 채널 환경변수 설정" -ForegroundColor Green
Write-Host "=" * 60

# 현재 상태 확인
Write-Host "📊 현재 설정 상태:" -ForegroundColor Yellow
$channels = @{
    "Slack" = @{status = "✅ 성공"; reason = "Webhook URL 설정됨"}
    "Notion" = @{status = "❌ 실패"; reason = "스키마 불일치 또는 토큰 문제"}
    "Email" = @{status = "❌ 실패"; reason = "SMTP 환경변수 누락"}
    "Pushbullet" = @{status = "❌ 실패"; reason = "토큰 누락"}
}

foreach ($channel in $channels.Keys) {
    $config = $channels[$channel]
    Write-Host "   $($config.status) $channel : $($config.reason)" -ForegroundColor $(if ($config.status -eq "✅ 성공") { "Green" } else { "Red" })
}

Write-Host "`n🔧 설정 가이드:" -ForegroundColor Yellow

# 1. Notion 설정
Write-Host "`n📝 Notion 설정:" -ForegroundColor Cyan
Write-Host "   현재 NOTION_TOKEN: $($env:NOTION_TOKEN)" -ForegroundColor Gray
Write-Host "   현재 NOTION_DATABASE_ID: $($env:NOTION_DATABASE_ID)" -ForegroundColor Gray
Write-Host "   문제: 데이터베이스 스키마 불일치 (status=400)" -ForegroundColor Red
Write-Host "   해결책:" -ForegroundColor Yellow
Write-Host "   1. Notion 데이터베이스에서 실제 속성명 확인" -ForegroundColor White
Write-Host "   2. 'Name'과 'Description' 속성이 있는지 확인" -ForegroundColor White
Write-Host "   3. 없다면 다른 속성명으로 수정 필요" -ForegroundColor White

# 2. Email 설정
Write-Host "`n📧 Email 설정:" -ForegroundColor Cyan
Write-Host "   필요한 환경변수:" -ForegroundColor Yellow
Write-Host "   `$env:SMTP_HOST = 'smtp.gmail.com'" -ForegroundColor White
Write-Host "   `$env:SMTP_PORT = '587'" -ForegroundColor White
Write-Host "   `$env:SMTP_USER = 'your-email@gmail.com'" -ForegroundColor White
Write-Host "   `$env:SMTP_PASS = 'your-app-password'" -ForegroundColor White
Write-Host "   `$env:EMAIL_TO = 'recipient@example.com'" -ForegroundColor White
Write-Host "   `$env:EMAIL_FROM = 'sender@example.com'" -ForegroundColor White
Write-Host "   `$env:DISPATCH_EMAIL = '1'" -ForegroundColor White

# 3. Pushbullet 설정
Write-Host "`n📱 Pushbullet 설정:" -ForegroundColor Cyan
Write-Host "   필요한 환경변수:" -ForegroundColor Yellow
Write-Host "   `$env:PUSHBULLET_TOKEN = 'your-access-token'" -ForegroundColor White
Write-Host "   `$env:DISPATCH_PUSH = '1'" -ForegroundColor White
Write-Host "   설정 방법:" -ForegroundColor Yellow
Write-Host "   1. https://www.pushbullet.com/#settings/account 접속" -ForegroundColor White
Write-Host "   2. 'Create Access Token' 클릭" -ForegroundColor White
Write-Host "   3. 생성된 토큰을 환경변수에 설정" -ForegroundColor White

Write-Host "`n💡 설정 예시:" -ForegroundColor Green
Write-Host "   # Email 설정 예시" -ForegroundColor Cyan
Write-Host "   `$env:SMTP_HOST = 'smtp.gmail.com'" -ForegroundColor Gray
Write-Host "   `$env:SMTP_PORT = '587'" -ForegroundColor Gray
Write-Host "   `$env:SMTP_USER = 'your-email@gmail.com'" -ForegroundColor Gray
Write-Host "   `$env:SMTP_PASS = 'your-app-password'" -ForegroundColor Gray
Write-Host "   `$env:EMAIL_TO = 'recipient@example.com'" -ForegroundColor Gray
Write-Host "   `$env:EMAIL_FROM = 'sender@example.com'" -ForegroundColor Gray
Write-Host "   `$env:DISPATCH_EMAIL = '1'" -ForegroundColor Gray
Write-Host "   " -ForegroundColor Gray
Write-Host "   # Pushbullet 설정 예시" -ForegroundColor Cyan
Write-Host "   `$env:PUSHBULLET_TOKEN = 'o.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'" -ForegroundColor Gray
Write-Host "   `$env:DISPATCH_PUSH = '1'" -ForegroundColor Gray

Write-Host "`n🎯 현재 상황:" -ForegroundColor Green
Write-Host "   ✅ Slack: 완벽하게 작동 중" -ForegroundColor Green
Write-Host "   ⚠️  Notion: 스키마 수정 필요" -ForegroundColor Yellow
Write-Host "   ❌ Email: 환경변수 설정 필요" -ForegroundColor Red
Write-Host "   ❌ Pushbullet: 토큰 설정 필요" -ForegroundColor Red

Write-Host "`n💡 권장사항:" -ForegroundColor Green
Write-Host "   1. Slack이 이미 성공하므로 핵심 기능은 완료" -ForegroundColor White
Write-Host "   2. 필요에 따라 다른 채널들 추가 설정 가능" -ForegroundColor White
Write-Host "   3. 환경변수는 .env 파일에 저장하여 영구 설정 가능" -ForegroundColor White
