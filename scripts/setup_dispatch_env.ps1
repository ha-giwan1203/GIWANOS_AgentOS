# VELOS 디스패치 환경변수 설정 스크립트
# 사용법: .\scripts\setup_dispatch_env.ps1

Write-Host "🚀 VELOS 디스패치 환경변수 설정" -ForegroundColor Green
Write-Host "=" * 50

# 1. Slack 설정
Write-Host "📱 Slack 설정:" -ForegroundColor Yellow
$env:DISPATCH_SLACK = "1"
Write-Host "   DISPATCH_SLACK = 1 (활성화됨)"

# SLACK_BOT_TOKEN이 없으면 설정 안내
if (-not $env:SLACK_BOT_TOKEN) {
    Write-Host "   ⚠️  SLACK_BOT_TOKEN이 설정되지 않았습니다." -ForegroundColor Red
    Write-Host "   Slack App에서 Bot User OAuth Token을 설정하세요." -ForegroundColor Gray
} else {
    Write-Host "   ✅ SLACK_BOT_TOKEN 설정됨" -ForegroundColor Green
}

# 2. Notion 설정
Write-Host "📝 Notion 설정:" -ForegroundColor Yellow
$env:DISPATCH_NOTION = "1"
Write-Host "   DISPATCH_NOTION = 1 (활성화됨)"

if (-not $env:NOTION_TOKEN) {
    Write-Host "   ⚠️  NOTION_TOKEN이 설정되지 않았습니다." -ForegroundColor Red
    Write-Host "   Notion Integration에서 Internal Integration Token을 설정하세요." -ForegroundColor Gray
} else {
    Write-Host "   ✅ NOTION_TOKEN 설정됨" -ForegroundColor Green
}

if (-not $env:NOTION_DATABASE_ID) {
    Write-Host "   ⚠️  NOTION_DATABASE_ID가 설정되지 않았습니다." -ForegroundColor Red
    Write-Host "   Notion 데이터베이스 URL에서 ID를 추출하여 설정하세요." -ForegroundColor Gray
} else {
    Write-Host "   ✅ NOTION_DATABASE_ID 설정됨" -ForegroundColor Green
}

# 3. Email 설정
Write-Host "📧 Email 설정:" -ForegroundColor Yellow
$env:DISPATCH_EMAIL = "1"
Write-Host "   DISPATCH_EMAIL = 1 (활성화됨)"

# SMTP 설정 안내
$smtp_vars = @("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "EMAIL_TO", "EMAIL_FROM")
$missing_smtp = @()

foreach ($var in $smtp_vars) {
    if (-not (Get-Variable -Name "env:$var" -ErrorAction SilentlyContinue)) {
        $missing_smtp += $var
    }
}

if ($missing_smtp.Count -gt 0) {
    Write-Host "   ⚠️  다음 SMTP 환경변수가 설정되지 않았습니다:" -ForegroundColor Red
    foreach ($var in $missing_smtp) {
        Write-Host "      - $var" -ForegroundColor Gray
    }
    Write-Host "   예시 설정:" -ForegroundColor Gray
    Write-Host "   `$env:SMTP_HOST = 'smtp.gmail.com'" -ForegroundColor Cyan
    Write-Host "   `$env:SMTP_PORT = '587'" -ForegroundColor Cyan
    Write-Host "   `$env:SMTP_USER = 'your-email@gmail.com'" -ForegroundColor Cyan
    Write-Host "   `$env:SMTP_PASS = 'your-app-password'" -ForegroundColor Cyan
    Write-Host "   `$env:EMAIL_TO = 'recipient@example.com'" -ForegroundColor Cyan
    Write-Host "   `$env:EMAIL_FROM = 'sender@example.com'" -ForegroundColor Cyan
} else {
    Write-Host "   ✅ 모든 SMTP 환경변수 설정됨" -ForegroundColor Green
}

# 4. Pushbullet 설정
Write-Host "📱 Pushbullet 설정:" -ForegroundColor Yellow
$env:DISPATCH_PUSH = "1"
Write-Host "   DISPATCH_PUSH = 1 (활성화됨)"

if (-not $env:PUSHBULLET_TOKEN) {
    Write-Host "   ⚠️  PUSHBULLET_TOKEN이 설정되지 않았습니다." -ForegroundColor Red
    Write-Host "   Pushbullet 설정에서 Access Token을 설정하세요." -ForegroundColor Gray
} else {
    Write-Host "   ✅ PUSHBULLET_TOKEN 설정됨" -ForegroundColor Green
}

# 5. 설정 요약
Write-Host "=" * 50
Write-Host "📋 설정 요약:" -ForegroundColor Green

$channels = @{
    "Slack" = @{enabled = $true; token = $env:SLACK_BOT_TOKEN; channel = $env:SLACK_CHANNEL_ID}
    "Notion" = @{enabled = $true; token = $env:NOTION_TOKEN; database = $env:NOTION_DATABASE_ID}
    "Email" = @{enabled = $true; smtp = ($missing_smtp.Count -eq 0)}
    "Pushbullet" = @{enabled = $true; token = $env:PUSHBULLET_TOKEN}
}

foreach ($channel in $channels.Keys) {
    $config = $channels[$channel]
    $status = if ($config.enabled) { "✅" } else { "❌" }
    $ready = if ($config.token -or $config.smtp) { "준비됨" } else { "설정 필요" }
    Write-Host "   $status $channel : $ready" -ForegroundColor $(if ($config.token -or $config.smtp) { "Green" } else { "Red" })
}

Write-Host "=" * 50
Write-Host "💡 팁: 환경변수를 영구적으로 설정하려면 PowerShell 프로필에 추가하세요." -ForegroundColor Cyan
Write-Host "   또는 .env 파일에 설정하여 VELOS_LOAD_ENV=1로 로드하세요." -ForegroundColor Cyan
