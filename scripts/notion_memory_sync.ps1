# scripts/notion_memory_sync.ps1
$ErrorActionPreference = "Stop"

Write-Host "🧠 VELOS Notion 기억 저장소 동기화" -ForegroundColor Green
Write-Host "=" * 50

$results = @{}

# 1. Notion DB 구조화 저장
Write-Host "`n📊 Notion DB 구조화 저장 중..." -ForegroundColor Cyan
try {
    python scripts/notion_memory_db.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Notion DB 성공" -ForegroundColor Green
        $results["notion_db"] = "success"
    } else {
        Write-Host "❌ Notion DB 실패" -ForegroundColor Red
        $results["notion_db"] = "failed"
    }
} catch {
    Write-Host "❌ Notion DB 오류: $_" -ForegroundColor Red
    $results["notion_db"] = "error"
}

# 2. Notion Page 전문 저장
Write-Host "`n📄 Notion Page 전문 저장 중..." -ForegroundColor Cyan
try {
    python scripts/notion_memory_page.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Notion Page 성공" -ForegroundColor Green
        $results["notion_page"] = "success"
    } else {
        Write-Host "❌ Notion Page 실패" -ForegroundColor Red
        $results["notion_page"] = "failed"
    }
} catch {
    Write-Host "❌ Notion Page 오류: $_" -ForegroundColor Red
    $results["notion_page"] = "error"
}

# 결과 요약
Write-Host "`n📊 Notion 메모리 동기화 결과" -ForegroundColor Yellow
Write-Host "=" * 35

$success_count = 0
foreach ($component in $results.Keys) {
    $status = $results[$component]
    if ($status -eq "success") {
        Write-Host "✅ $component" -ForegroundColor Green
        $success_count++
    } elseif ($status -eq "failed") {
        Write-Host "❌ $component" -ForegroundColor Red
    } else {
        Write-Host "⚠️  $component" -ForegroundColor Yellow
    }
}

Write-Host "`n🎯 성공률: $success_count/2 ($([math]::Round($success_count/2*100, 1))%)" -ForegroundColor $(if ($success_count -eq 2) { "Green" } elseif ($success_count -eq 1) { "Yellow" } else { "Red" })

# 상세 설명
Write-Host "`n📖 Notion 기억 저장소 구조:" -ForegroundColor Blue
Write-Host "   📊 DB: 구조화된 기억 (태스크/명령/태그별)" -ForegroundColor White
Write-Host "   📄 Page: 전문 저장 (보고서/로그 전체)" -ForegroundColor White
Write-Host "   🔄 양방향: 로컬 ↔ Notion 완전 동기화" -ForegroundColor White

# 종료 코드
if ($success_count -eq 2) {
    Write-Host "`n🎉 Notion 기억 저장소 완전 동기화!" -ForegroundColor Green
    exit 0
} elseif ($success_count -eq 1) {
    Write-Host "`n⚠️  부분적 동기화 완료" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "`n💥 동기화 실패" -ForegroundColor Red
    exit 2
}
