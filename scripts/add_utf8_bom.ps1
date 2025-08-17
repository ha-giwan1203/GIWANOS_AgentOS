# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# PowerShell 스크립트들에 UTF-8 BOM 추가 유틸리티
$ErrorActionPreference = "Stop"

Write-Host "[VELOS] UTF-8 BOM 추가 유틸리티 시작..."

# 현재 디렉토리의 모든 .ps1 파일 찾기
$ps1Files = Get-ChildItem -Path ".\scripts\*.ps1" -File

Write-Host "총 $($ps1Files.Count)개의 PowerShell 스크립트를 찾았습니다."

$processedCount = 0
$skippedCount = 0

foreach ($file in $ps1Files) {
    try {
        # 파일의 첫 3바이트 읽기
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)

        if ($bytes.Length -ge 3) {
            $firstThree = $bytes[0..2]
            $hexString = ($firstThree | ForEach-Object { '{0:X2}' -f $_ }) -join ' '

            if ($hexString -eq "EF BB BF") {
                Write-Host "[SKIP] $($file.Name) - 이미 UTF-8 BOM이 있습니다."
                $skippedCount++
            } else {
                # BOM이 없으면 추가
                $content = Get-Content $file.FullName -Raw
                [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.Encoding]::UTF8)
                Write-Host "[OK] $($file.Name) - UTF-8 BOM 추가됨"
                $processedCount++
            }
        } else {
            Write-Host "[SKIP] $($file.Name) - 파일이 너무 작습니다."
            $skippedCount++
        }
    } catch {
        Write-Host "[ERROR] $($file.Name) - 처리 실패: $_"
    }
}

Write-Host "`n=== 처리 결과 ==="
Write-Host "처리된 파일: $processedCount"
Write-Host "건너뛴 파일: $skippedCount"
Write-Host "총 파일: $($ps1Files.Count)"

Write-Host "`n[DONE] UTF-8 BOM 추가 완료!"
