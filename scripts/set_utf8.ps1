# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# PowerShell 출력·입력 UTF-8
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding           = [System.Text.UTF8Encoding]::new($false)

# Python이 터미널 인코딩을 확실히 UTF-8로 쓰게
$env:PYTHONUTF8      = "1"
$env:PYTHONIOENCODING= "utf-8"

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

# (cmd 창 겸용) 코드 페이지 강제
try {
    chcp 65001 > $null
    Write-Host "[OK] Code page set to UTF-8 (65001)"
} catch {
    Write-Host "[WARN] Failed to set code page: $_"
}

Write-Host "[OK] UTF-8 encoding configured for PowerShell and Python"
Write-Host "[INFO] OutputEncoding: $OutputEncoding"
Write-Host "[INFO] PYTHONUTF8: $env:PYTHONUTF8"
Write-Host "[INFO] PYTHONIOENCODING: $env:PYTHONIOENCODING"

# 테스트 출력
Write-Host "`n=== 한글 테스트 ==="
Write-Host "안녕하세요! VELOS 환경 변수 설정이 완료되었습니다."
Write-Host "이제 한글이 정상적으로 출력됩니다."
