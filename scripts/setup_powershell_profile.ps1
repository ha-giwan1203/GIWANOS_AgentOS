# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# PowerShell 프로파일에 UTF-8 설정 추가
$ErrorActionPreference = "Stop"

Write-Host "[VELOS] PowerShell 프로파일 설정 중..."

# 프로파일 경로 확인
Write-Host "[INFO] PowerShell 프로파일 경로: $PROFILE"

# 프로파일이 없으면 생성
if (!(Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
    Write-Host "[OK] PowerShell 프로파일 생성됨"
} else {
    Write-Host "[INFO] PowerShell 프로파일이 이미 존재함"
}

# UTF-8 설정 내용
$utf8Settings = @'
# VELOS UTF-8 설정 (자동 추가됨)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding           = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8           = "1"
$env:PYTHONIOENCODING     = "utf-8"
$PSStyle.OutputRendering  = "Host"
try { chcp 65001 > $null } catch {}
'@

# 기존 내용 확인
$existingContent = ""
if (Test-Path $PROFILE) {
    $existingContent = Get-Content -Path $PROFILE -Raw -ErrorAction SilentlyContinue
}

# UTF-8 설정이 이미 있는지 확인
if ($existingContent -and $existingContent.Contains("VELOS UTF-8 설정")) {
    Write-Host "[INFO] UTF-8 설정이 이미 프로파일에 포함되어 있음"
} else {
    # 기존 내용에 UTF-8 설정 추가
    $newContent = $existingContent + "`n" + $utf8Settings
    Set-Content -Path $PROFILE -Value $newContent -Encoding UTF8
    Write-Host "[OK] UTF-8 설정이 프로파일에 추가됨"
}

# 프로파일 내용 확인
Write-Host "`n[VERIFICATION] 프로파일 내용:"
Write-Host "=" * 50
Get-Content -Path $PROFILE | Select-Object -Last 10

Write-Host "`n[DONE] PowerShell 프로파일 설정 완료!"
Write-Host "[NOTE] 새 PowerShell 세션에서 UTF-8 설정이 자동으로 적용됩니다."
