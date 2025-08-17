# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

$ErrorActionPreference = "Stop"

# VELOS-MasterLoop 태스크 생성 스크립트
Write-Host "=== VELOS-MasterLoop 태스크 생성 ===" -ForegroundColor Cyan

# 1. 기존 태스크 삭제
Write-Host "1. 기존 태스크 삭제..." -ForegroundColor Yellow
try {
    schtasks /delete /tn "VELOS-MasterLoop" /f 2>$null
    Write-Host "   ✅ 기존 태스크 삭제 완료" -ForegroundColor Green
}
catch {
    Write-Host "   ℹ️  기존 태스크 없음" -ForegroundColor Gray
}

# 2. 새 태스크 생성
Write-Host "2. 새 태스크 생성..." -ForegroundColor Yellow
$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\giwanos\scripts\velos_master_loop_wrapper.ps1'

try {
    schtasks /create /tn "VELOS-MasterLoop" /sc minute /mo 10 /tr $cmd /f
    Write-Host "   ✅ VELOS-MasterLoop 태스크 생성 완료" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 태스크 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 관리자 권한으로 실행하거나 수동으로 생성하세요." -ForegroundColor Yellow
    exit 1
}

# 3. 태스크 확인
Write-Host "3. 태스크 확인..." -ForegroundColor Yellow
try {
    $task = schtasks /query /tn "VELOS-MasterLoop" /fo list 2>$null
    if ($task) {
        Write-Host "   ✅ 태스크 확인 완료" -ForegroundColor Green
        Write-Host "   📋 태스크 정보:" -ForegroundColor Cyan
        $task | Select-String -Pattern "TaskName|Schedule|Next Run Time|Last Result" | ForEach-Object { Write-Host "      $_" }
    }
    else {
        Write-Host "   ⚠️  태스크 확인 실패" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ⚠️  태스크 확인 실패: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "=== VELOS-MasterLoop 태스크 생성 완료 ===" -ForegroundColor Cyan
