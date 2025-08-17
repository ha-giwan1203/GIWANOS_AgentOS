# VELOS 환경변수 설정 스크립트
# 사용법: .\scripts\setup_env_variables.ps1

Write-Host "🔧 VELOS 환경변수 설정" -ForegroundColor Green
Write-Host "=" * 50

# 현재 설정된 환경변수 확인
Write-Host "📊 현재 설정된 환경변수:" -ForegroundColor Yellow
$current_vars = @{
    "EMAIL_PASSWORD" = $env:EMAIL_PASSWORD
    "NOTION_TOKEN" = $env:NOTION_TOKEN
    "SLACK_WEBHOOK_URL" = $env:SLACK_WEBHOOK_URL
}

foreach ($var in $current_vars.Keys) {
    $value = $current_vars[$var]
    if ($value) {
        Write-Host "   ✅ $var : 설정됨" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $var : 설정 안됨" -ForegroundColor Red
    }
}

Write-Host "`n🔧 누락된 환경변수 설정:" -ForegroundColor Yellow

# Email 설정
Write-Host "`n📧 Email 설정 (네이버 기준):" -ForegroundColor Cyan
Write-Host "   현재 EMAIL_PASSWORD: $($env:EMAIL_PASSWORD)" -ForegroundColor Gray

$smtp_host = Read-Host "   SMTP_HOST (기본값: smtp.naver.com)"
if (-not $smtp_host) { $smtp_host = "smtp.naver.com" }

$smtp_port = Read-Host "   SMTP_PORT (기본값: 587)"
if (-not $smtp_port) { $smtp_port = "587" }

$smtp_user = Read-Host "   SMTP_USER (네이버 이메일 주소)"
$smtp_pass = Read-Host "   SMTP_PASS (앱 비밀번호)" -AsSecureString
$email_to = Read-Host "   EMAIL_TO (받는 사람 이메일)"
$email_from = Read-Host "   EMAIL_FROM (보내는 사람 이메일, 기본값: SMTP_USER)"
if (-not $email_from) { $email_from = $smtp_user }

# 환경변수 설정
$env:SMTP_HOST = $smtp_host
$env:SMTP_PORT = $smtp_port
$env:SMTP_USER = $smtp_user
$env:SMTP_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtp_pass))
$env:EMAIL_TO = $email_to
$env:EMAIL_FROM = $email_from
$env:DISPATCH_EMAIL = "1"

Write-Host "   ✅ Email 환경변수 설정 완료" -ForegroundColor Green

# Pushbullet 설정
Write-Host "`n📱 Pushbullet 설정:" -ForegroundColor Cyan
$push_token = Read-Host "   PUSHBULLET_TOKEN (https://www.pushbullet.com/#settings/account에서 생성)"
if ($push_token) {
    $env:PUSHBULLET_TOKEN = $push_token
    $env:DISPATCH_PUSH = "1"
    Write-Host "   ✅ Pushbullet 환경변수 설정 완료" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Pushbullet 설정 건너뜀" -ForegroundColor Yellow
}

# Notion 설정
Write-Host "`n📝 Notion 설정:" -ForegroundColor Cyan
Write-Host "   현재 NOTION_TOKEN: $($env:NOTION_TOKEN)" -ForegroundColor Gray
$notion_db = Read-Host "   NOTION_DATABASE_ID (데이터베이스 ID)"
if ($notion_db) {
    $env:NOTION_DATABASE_ID = $notion_db
    $env:DISPATCH_NOTION = "1"
    Write-Host "   ✅ Notion 환경변수 설정 완료" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Notion 설정 건너뜀" -ForegroundColor Yellow
}

# .env 파일에 저장
Write-Host "`n💾 .env 파일에 저장:" -ForegroundColor Yellow
$env_content = @"
# VELOS Email 설정
SMTP_HOST=$smtp_host
SMTP_PORT=$smtp_port
SMTP_USER=$smtp_user
SMTP_PASS=$($env:SMTP_PASS)
EMAIL_TO=$email_to
EMAIL_FROM=$email_from
DISPATCH_EMAIL=1

# VELOS Pushbullet 설정
PUSHBULLET_TOKEN=$($env:PUSHBULLET_TOKEN)
DISPATCH_PUSH=1

# VELOS Notion 설정
NOTION_DATABASE_ID=$($env:NOTION_DATABASE_ID)
DISPATCH_NOTION=1

# 기존 설정들
EMAIL_PASSWORD=$($env:EMAIL_PASSWORD)
NOTION_TOKEN=$($env:NOTION_TOKEN)
SLACK_WEBHOOK_URL=$($env:SLACK_WEBHOOK_URL)
VELOS_SLACK_WEBHOOK=$($env:VELOS_SLACK_WEBHOOK)
SLACK_CHANNEL=$($env:SLACK_CHANNEL)
"@

$env_file = "configs\.env"
$env_content | Out-File -FilePath $env_file -Encoding UTF8
Write-Host "   ✅ $env_file 파일에 저장 완료" -ForegroundColor Green

# 테스트 실행
Write-Host "`n🧪 디스패치 테스트 실행:" -ForegroundColor Yellow
python scripts\dispatch_report.py

Write-Host "`n🎯 설정 완료!" -ForegroundColor Green
Write-Host "   환경변수가 .env 파일에 저장되었습니다." -ForegroundColor White
Write-Host "   다음 실행 시에도 설정이 유지됩니다." -ForegroundColor White
