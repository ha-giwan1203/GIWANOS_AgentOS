# [ACTIVE] VELOS 로그 통합 시스템 - 로그 파일 통합 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

Write-Host "=== VELOS 로그 파일 통합 ===" -ForegroundColor Yellow

# 로그 통합 설정
$sourceLogsDir = "C:\giwanos\logs"
$targetLogsDir = "C:\giwanos\data\logs"
$backupDir = "C:\giwanos\data\logs\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Write-Host "`n[1] 대상 디렉토리 확인..." -ForegroundColor Cyan
if (Test-Path $sourceLogsDir) {
    Write-Host "  ✅ 소스 로그 디렉토리 존재: $sourceLogsDir" -ForegroundColor Green
    $sourceFiles = Get-ChildItem $sourceLogsDir -File
    Write-Host "  📁 소스 파일 수: $($sourceFiles.Count)" -ForegroundColor Cyan
} else {
    Write-Host "  ❌ 소스 로그 디렉토리 없음: $sourceLogsDir" -ForegroundColor Red
    exit 1
}

if (Test-Path $targetLogsDir) {
    Write-Host "  ✅ 대상 로그 디렉토리 존재: $targetLogsDir" -ForegroundColor Green
} else {
    Write-Host "  ❌ 대상 로그 디렉토리 없음: $targetLogsDir" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2] 백업 디렉토리 생성..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "  📁 백업 디렉토리 생성: $backupDir" -ForegroundColor Green

Write-Host "`n[3] 로그 파일 통합..." -ForegroundColor Cyan
$movedFiles = @()

foreach ($file in $sourceFiles) {
    $sourcePath = $file.FullName
    $targetPath = Join-Path $targetLogsDir $file.Name
    
    # 파일명 충돌 처리
    if (Test-Path $targetPath) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $newName = "$($file.BaseName)_merged_$timestamp$($file.Extension)"
        $targetPath = Join-Path $targetLogsDir $newName
        Write-Host "  🔄 파일명 충돌 처리: $($file.Name) → $newName" -ForegroundColor Yellow
    }
    
    try {
        # 파일 이동
        Move-Item $sourcePath $targetPath -Force
        $movedFiles += $file.Name
        Write-Host "  ✅ 이동 완료: $($file.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ 이동 실패: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[4] 빈 로그 디렉토리 정리..." -ForegroundColor Cyan
if ((Get-ChildItem $sourceLogsDir -File).Count -eq 0) {
    try {
        Remove-Item $sourceLogsDir -Force
        Write-Host "  ✅ 빈 로그 디렉토리 삭제: $sourceLogsDir" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️ 디렉토리 삭제 실패: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️ 로그 디렉토리에 남은 파일이 있습니다." -ForegroundColor Yellow
}

Write-Host "`n[5] 통합 결과 요약..." -ForegroundColor Cyan
Write-Host "  📊 이동된 파일 수: $($movedFiles.Count)" -ForegroundColor Green
Write-Host "  📁 대상 디렉토리: $targetLogsDir" -ForegroundColor Cyan
Write-Host "  📁 백업 디렉토리: $backupDir" -ForegroundColor Cyan

Write-Host "`n[6] 로그 디렉토리 구조 확인..." -ForegroundColor Cyan
$targetFiles = Get-ChildItem $targetLogsDir -File | Group-Object Extension | Sort-Object Count -Descending
foreach ($group in $targetFiles) {
    Write-Host "  $($group.Name): $($group.Count)개 파일" -ForegroundColor Cyan
}

Write-Host "`n=== VELOS 로그 통합 완료 ===" -ForegroundColor Green
Write-Host "모든 로그 파일이 $targetLogsDir로 통합되었습니다." -ForegroundColor Yellow

