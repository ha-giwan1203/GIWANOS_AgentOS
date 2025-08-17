# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Environment Variables Setup
$ErrorActionPreference = "Stop"

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

try {
    chcp 65001 > $null
} catch {
    # 코드 페이지 설정 실패 시 무시
}

# Environment variables to set
$vars = @{
    'VELOS_ROOT' = 'C:\giwanos'
    'VELOS_DB' = 'C:\giwanos\velos.db'
    'VELOS_MEM_FAST' = 'C:\giwanos\data\memory\fast_ctx.jsonl'
    'VELOS_LOG_DIR' = 'C:\giwanos\data\logs'
    'VELOS_REPORT_DIR' = 'C:\giwanos\data\reports'
    'VELOS_SNAPSHOT_DIR' = 'C:\giwanos\data\snapshots'
    'VELOS_MEMORY_ONLY' = '1'
}

Write-Host "[VELOS] Setting environment variables..."

# Check if running as administrator
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$IsAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Host "[INFO] Running as Administrator: $IsAdmin"

# Set environment variables
foreach($key in $vars.Keys) {
    $value = $vars[$key]

    try {
        if($IsAdmin) {
            [Environment]::SetEnvironmentVariable($key, $value, 'Machine')
            Write-Host "[OK] Set $key to Machine scope"
        } else {
            [Environment]::SetEnvironmentVariable($key, $value, 'User')
            Write-Host "[OK] Set $key to User scope"
        }

        # Set for current process
        Set-Variable -Name "env:$key" -Value $value -Scope Global
        Write-Host "[OK] Set $key for current process"

    } catch {
        Write-Host "[ERROR] Failed to set $key : $_"
    }
}

Write-Host "`n[VERIFICATION] Current environment variables:"
Write-Host "=========================================="

foreach($key in $vars.Keys) {
    $procValue = [Environment]::GetEnvironmentVariable($key, 'Process')
    $userValue = [Environment]::GetEnvironmentVariable($key, 'User')
    $machineValue = [Environment]::GetEnvironmentVariable($key, 'Machine')

    Write-Host "$key = $procValue (Proc=$procValue; User=$userValue; Machine=$machineValue)"
}

Write-Host "`n[DONE] VELOS environment variables configured!"
Write-Host "[NOTE] Machine scope changes require new sessions to take effect."
