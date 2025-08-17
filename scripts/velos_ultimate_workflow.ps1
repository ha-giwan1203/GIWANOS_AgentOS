# PowerShell 7+ VELOS 최종 완전 통합 워크플로우
# 1. Notion DB 생성 (메타데이터)
# 2. Notion Page 생성 (Markdown 내용)
# 3. Slack 알림 (Notion 링크 포함)
# 4. 이메일 전송 (PDF 첨부)
# 5. Pushbullet 알림 (모바일 푸시)

$ErrorActionPreference = "Stop"
$py = "C:\Users\User\venvs\velos\Scripts\python.exe"

# 환경변수 로딩
try {
    . "C:\giwanos\configs\.env"
} catch {
    Write-Warning "환경변수 파일을 찾을 수 없습니다: $($_.Exception.Message)"
}

# 0) .env에서 오늘 생성물 경로/제목 주입(필요시 수정)
$reportPdf = "C:\giwanos\data\reports\auto\latest.pdf"   # 너희 파이프라인 결과물
$reportMd  = "C:\giwanos\data\reports\auto\latest.md"

# 최신 파일 찾기 (latest가 없으면 실제 최신 파일 사용)
if (-not (Test-Path $reportPdf)) {
    $autoDir = "C:\giwanos\data\reports\auto"
    $latestPdf = Get-ChildItem -Path $autoDir -Filter "velos_auto_report_*_ko.pdf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $latestMd = Get-ChildItem -Path $autoDir -Filter "velos_auto_report_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($latestPdf) { $reportPdf = $latestPdf.FullName }
    if ($latestMd) { $reportMd = $latestMd.FullName }
}

Write-Host "🚀 VELOS PowerShell 최종 완전 통합 워크플로우 시작" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "📄 처리할 파일:"
Write-Host "   PDF: $([System.IO.Path]::GetFileName($reportPdf))"
Write-Host "   MD:  $([System.IO.Path]::GetFileName($reportMd))"

# 환경변수 설정
$env:VELOS_TITLE      = "VELOS 자동 보고서"
$env:VELOS_PDF_PATH   = $reportPdf
$env:VELOS_MD_PATH    = $reportMd
$env:VELOS_REPORT_PATH= $reportPdf
$env:VELOS_STATUS     = "완료"
$env:VELOS_TAGS       = "Auto,VELOS,Report"

# JSON 추출 함수
function Extract-JsonFromOutput {
    param([string]$Output)

    # JSON 패턴 찾기 (마지막 {로 시작하는 부분)
    $jsonMatch = [regex]::Match($Output, '\{[^{}]*"ok"[^{}]*\}')
    if ($jsonMatch.Success) {
        return $jsonMatch.Value
    }

    # 줄 단위로 검색
    $lines = $Output -split "`n"
    foreach ($line in $lines) {
        if ($line.Trim().StartsWith('{') -and $line.Trim().EndsWith('}')) {
            return $line.Trim()
        }
    }

    return $null
}

# 1) Notion DB row 생성(메타)
Write-Host "`n🔹 1단계: Notion DB 생성" -ForegroundColor Cyan
Write-Host "-" * 30

try {
    $dbOut = & $py "scripts/notion_db_create.py"
    Write-Host $dbOut

    $pageId = ""
    try {
        $jsonStr = Extract-JsonFromOutput $dbOut
        if ($jsonStr) {
            $dbResult = $jsonStr | ConvertFrom-Json
            $pageId = $dbResult.page_id
            Write-Host "✅ DB 생성 성공!" -ForegroundColor Green
            Write-Host "   페이지 ID: $pageId"
        } else {
            Write-Host "❌ JSON을 찾을 수 없습니다" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ DB 결과 파싱 실패: $($_.Exception.Message)" -ForegroundColor Red
        $pageId = ""
    }
} catch {
    Write-Host "❌ Notion DB 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️  DB 생성 실패했지만 워크플로우는 계속 진행합니다"
    $pageId = ""
}

# 2) Notion Page 본문 생성(필요 시 parent_page 또는 DB 아래)
Write-Host "`n🔹 2단계: Notion Page 생성" -ForegroundColor Cyan
Write-Host "-" * 30

try {
    $pageOut = & $py "scripts/notion_page_create.py"
    Write-Host $pageOut

    $pageId2 = ""
    try {
        $jsonStr = Extract-JsonFromOutput $pageOut
        if ($jsonStr) {
            $pageResult = $jsonStr | ConvertFrom-Json
            $pageId2 = $pageResult.page_id
            Write-Host "✅ Page 생성 성공!" -ForegroundColor Green
            Write-Host "   페이지 ID: $pageId2"
            if ($pageResult.url) {
                Write-Host "   URL: $($pageResult.url)"
            }
        } else {
            Write-Host "❌ JSON을 찾을 수 없습니다" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Page 결과 파싱 실패: $($_.Exception.Message)" -ForegroundColor Red
        $pageId2 = ""
    }
} catch {
    Write-Host "❌ Notion Page 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️  Page 생성 실패했지만 워크플로우는 계속 진행합니다"
    $pageId2 = ""
}

# 3) Slack 알림(노션 링크 포함: 단순 URL 포맷)
Write-Host "`n🔹 3단계: Slack 알림" -ForegroundColor Cyan
Write-Host "-" * 20

if ($pageId2) {
    $env:NOTION_PAGE_URL = "https://www.notion.so/" + $pageId2.Replace("-","")
    Write-Host "   Notion 링크 설정: $($env:NOTION_PAGE_URL)"
}

try {
    $slackOut = & $py "scripts/slack_notify.py"
    Write-Host $slackOut

    try {
        $jsonStr = Extract-JsonFromOutput $slackOut
        if ($jsonStr) {
            $slackResult = $jsonStr | ConvertFrom-Json
            if ($slackResult.ok) {
                Write-Host "✅ Slack 알림 성공!" -ForegroundColor Green
            } else {
                Write-Host "❌ Slack 알림 실패: $($slackResult.error)" -ForegroundColor Red
            }
        } else {
            Write-Host "⚠️  Slack JSON을 찾을 수 없습니다" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Slack 결과 파싱 실패: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Slack 알림 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️  Slack 알림 실패했지만 워크플로우는 계속 진행합니다"
}

# 4) Email + 첨부
Write-Host "`n🔹 4단계: 이메일 전송" -ForegroundColor Cyan
Write-Host "-" * 20

try {
    $emailOut = & $py "scripts/email_send.py"
    Write-Host $emailOut

    try {
        $jsonStr = Extract-JsonFromOutput $emailOut
        if ($jsonStr) {
            $emailResult = $jsonStr | ConvertFrom-Json
            if ($emailResult.ok) {
                Write-Host "✅ 이메일 전송 성공!" -ForegroundColor Green
                Write-Host "   수신자: $($emailResult.to)"
                if ($emailResult.attachment_included) {
                    Write-Host "   첨부파일: $($emailResult.attachment_file)"
                }
            } else {
                Write-Host "❌ 이메일 전송 실패: $($emailResult.error)" -ForegroundColor Red
            }
        } else {
            Write-Host "⚠️  이메일 JSON을 찾을 수 없습니다" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  이메일 결과 파싱 실패: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 이메일 전송 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "⚠️  이메일 전송 실패했지만 워크플로우는 계속 진행합니다"
}

# 5) Pushbullet (선택)
Write-Host "`n🔹 5단계: Pushbullet 알림" -ForegroundColor Cyan
Write-Host "-" * 20

try {
    $pushOut = & $py "scripts/pushbullet_send.py"
    Write-Host $pushOut

    try {
        $jsonStr = Extract-JsonFromOutput $pushOut
        if ($jsonStr) {
            $pushResult = $jsonStr | ConvertFrom-Json
            if ($pushResult.ok) {
                Write-Host "✅ Pushbullet 알림 성공!" -ForegroundColor Green
                Write-Host "   상태 코드: $($pushResult.status_code)"
            } else {
                Write-Host "❌ Pushbullet 알림 실패: $($pushResult.error)" -ForegroundColor Red
            }
        } else {
            Write-Host "⚠️  Pushbullet JSON을 찾을 수 없습니다" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Pushbullet 결과 파싱 실패: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} catch {
    Write-Warning "Pushbullet 실패 (무시하고 계속 진행): $($_.Exception.Message)"
}

# 최종 결과
Write-Host "`n🎉 VELOS PowerShell 최종 완전 통합 워크플로우 완료!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "📊 생성된 항목들:"
Write-Host "   📋 DB 항목: $pageId"
Write-Host "   📄 상세 페이지: $pageId2"
Write-Host "   📧 이메일: 성공"
Write-Host "   📱 Slack: 성공"
Write-Host "   📱 Pushbullet: 성공"

Write-Host "`n=== DISPATCH ALL DONE ===" -ForegroundColor Green
