# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# BOM 제거 유틸리티 (Python/JSON/YAML 파일용)
$ErrorActionPreference = "Stop"

Write-Host "[VELOS] UTF-8 BOM 제거 유틸리티 시작..."

# BOM이 있는 파일들을 찾기
$targets = @("*.py", "*.json", "*.jsonl", "*.yml", "*.yaml", "*.toml", "*.csv")
$filesWithBOM = @()

Write-Host "BOM이 있는 파일들을 스캔 중..."

Get-ChildItem -Recurse -File -Include $targets | ForEach-Object {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $filesWithBOM += $_.FullName
            Write-Host "[FOUND] $($_.Name) - BOM 발견"
        }
    } catch {
        Write-Host "[ERROR] $($_.Name) - 읽기 실패: $_"
    }
}

Write-Host "`n총 $($filesWithBOM.Count)개의 BOM 파일을 발견했습니다."

if ($filesWithBOM.Count -eq 0) {
    Write-Host "[INFO] BOM이 있는 파일이 없습니다."
    exit 0
}

# 사용자 확인
$response = Read-Host "이 파일들을 무BOM UTF-8로 변환하시겠습니까? (y/N)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "[CANCELLED] 작업이 취소되었습니다."
    exit 0
}

# BOM 제거 작업
$processedCount = 0
$errorCount = 0

foreach ($file in $filesWithBOM) {
    try {
        # 파일 내용 읽기 (BOM 제외)
        $content = Get-Content $file -Raw -Encoding UTF8
        if ($content -eq $null) {
            # UTF8로 읽기 실패 시 다른 방법 시도
            $bytes = [System.IO.File]::ReadAllBytes($file)
            $content = [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
        }

        # 무BOM UTF-8로 다시 쓰기
        [System.IO.File]::WriteAllText($file, $content, [System.Text.Encoding]::UTF8)

        Write-Host "[OK] $([System.IO.Path]::GetFileName($file)) - BOM 제거됨"
        $processedCount++

    } catch {
        Write-Host "[ERROR] $([System.IO.Path]::GetFileName($file)) - 처리 실패: $_"
        $errorCount++
    }
}

Write-Host "`n=== 처리 결과 ==="
Write-Host "처리된 파일: $processedCount"
Write-Host "오류 발생: $errorCount"
Write-Host "총 파일: $($filesWithBOM.Count)"

Write-Host "`n[DONE] UTF-8 BOM 제거 완료!"
