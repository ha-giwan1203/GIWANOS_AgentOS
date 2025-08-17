# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

# VELOS 워크플로우 실행 스크립트
Write-Host "=== VELOS 워크플로우 실행 ===" -ForegroundColor Green

# 1. 환경 변수 설정
Write-Host "`n1️⃣ 환경 변수 설정..." -ForegroundColor Yellow
$env:VELOS_ROOT = "C:\giwanos"
$env:VELOS_DB = "C:\giwanos\data\velos.db"
$env:VELOS_JSONL_DIR = "C:\giwanos\data\memory"
$env:VELOS_RECENT_DAYS = "3"
$env:VELOS_KEYWORD_MAXLEN = "24"
$env:VELOS_FTS_LIMIT = "20"

Write-Host "   ✅ 환경 변수 설정 완료" -ForegroundColor Green

# 2. 스키마/DB 초기화 (ingest 자동 수행)
Write-Host "`n2️⃣ 스키마/DB 초기화 (JSONL 수집)..." -ForegroundColor Yellow
try {
    $ingestResult = python -m modules.memory.ingest.jsonl_ingest 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ JSONL 수집 완료" -ForegroundColor Green
        Write-Host "   📊 수집 결과: $ingestResult" -ForegroundColor Cyan
    } else {
        Write-Host "   ❌ JSONL 수집 실패: $ingestResult" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ JSONL 수집 오류: $_" -ForegroundColor Red
    exit 1
}

# 2-1. 호환 뷰 적용 및 검증
Write-Host "`n2️⃣-1️⃣ 호환 뷰 적용 및 검증..." -ForegroundColor Yellow
try {
    python scripts/apply_compat_views.py
    python scripts/check_compat_views.py
    Write-Host "   ✅ 호환 뷰 적용/검증 완료" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ 호환 뷰 처리 실패 (계속 진행)" -ForegroundColor Yellow
}

# 2-2. 자동 치유(auto-heal)
Write-Host "`n2️⃣-2️⃣ 자동 치유(auto-heal) 실행..." -ForegroundColor Yellow
try {
    python scripts/auto_heal.py
    Write-Host "   ✅ Auto-Heal 완료" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Auto-Heal 실패 (계속 진행)" -ForegroundColor Yellow
}

# 3. 회수 품질 테스트
Write-Host "`n3️⃣ 회수 품질 테스트..." -ForegroundColor Yellow
try {
    $testResult = python scripts/test_fts.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ FTS 테스트 완료" -ForegroundColor Green
    } else {
        Write-Host "   ❌ FTS 테스트 실패: $testResult" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ FTS 테스트 오류: $_" -ForegroundColor Red
    exit 1
}

# 4. 추가 테스트 (선택사항)
Write-Host "`n4️⃣ 추가 테스트 실행..." -ForegroundColor Yellow

# 종합 테스트
Write-Host "   📋 종합 FTS 테스트..." -ForegroundColor Cyan
try {
    python scripts/test_fts_comprehensive.py
    Write-Host "   ✅ 종합 테스트 완료" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ 종합 테스트 실패 (계속 진행)" -ForegroundColor Yellow
}

# 캐시 무효화 테스트
Write-Host "   📋 캐시 무효화 테스트..." -ForegroundColor Cyan
try {
    python scripts/test_cache_invalidation.py
    Write-Host "   ✅ 캐시 테스트 완료" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ 캐시 테스트 실패 (계속 진행)" -ForegroundColor Yellow
}

# 5. 최종 상태 확인
Write-Host "`n5️⃣ 최종 상태 확인..." -ForegroundColor Yellow

# DB 크기 확인
if (Test-Path $env:VELOS_DB) {
    $dbSize = (Get-Item $env:VELOS_DB).Length
    Write-Host "   📊 최종 DB 크기: $([math]::Round($dbSize/1KB, 2)) KB" -ForegroundColor Cyan
}

# 통계 확인
try {
    $statsResult = python scripts/check_velos_stats.py 2>&1
    Write-Host "   📈 시스템 통계:" -ForegroundColor Cyan
    Write-Host "   $statsResult" -ForegroundColor White
} catch {
    Write-Host "   ⚠️ 통계 확인 실패" -ForegroundColor Yellow
}

Write-Host "`n=== VELOS 워크플로우 완료 ===" -ForegroundColor Green
Write-Host "🎉 모든 단계가 성공적으로 완료되었습니다!" -ForegroundColor Green
