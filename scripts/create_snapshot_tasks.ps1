# ================================
# VELOS 운영 철학 선언문
# - 파일명 절대 변경 금지
# - 거짓코드 절대 금지
# - 모든 결과는 자가 검증 후 저장
# ================================

# === VELOS: 스냅샷 스케줄 태스크 생성 ===
# 스냅샷 카탈로그 및 무결성 검증을 위한 스케줄 태스크를 생성합니다.

try {
    Write-Host "[VELOS] Creating snapshot schedule tasks..." -ForegroundColor Green

    # 경로 고정
    $ROOT = "C:\giwanos"
    $PY = Join-Path $ROOT ".venv_link\Scripts\python.exe"

    # Python 경로 확인
    if (-not (Test-Path $PY)) {
        Write-Host "[ERROR] Python executable not found: $PY" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Python path verified: $PY" -ForegroundColor Green

    # 1) 기존 태스크 삭제 (존재하는 경우)
    Write-Host "1. Removing existing tasks..." -ForegroundColor Yellow

    $existing_tasks = @("VELOS Snapshot Catalog", "VELOS Snapshot Integrity")

    foreach ($task_name in $existing_tasks) {
        $task_exists = schtasks /query /tn $task_name 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   Removing existing task: $task_name" -ForegroundColor Cyan
            schtasks /delete /tn $task_name /f 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Task removed: $task_name" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️ Failed to remove task: $task_name" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "   Task not found: $task_name" -ForegroundColor Gray
        }
    }

    # 2) 카탈로그 갱신 태스크 생성 (매일 새벽 03:03)
    Write-Host "2. Creating VELOS Snapshot Catalog task..." -ForegroundColor Yellow

    $catalog_command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"& '$PY' '$ROOT\scripts\snapshot_catalog.py' --all`""

    Write-Host "   Command: $catalog_command" -ForegroundColor Cyan

    schtasks /create /tn "VELOS Snapshot Catalog" /sc daily /st 03:03 `
        /ru SYSTEM /rl HIGHEST `
        /tr $catalog_command `
        /f

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ VELOS Snapshot Catalog task created successfully" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ Failed to create VELOS Snapshot Catalog task" -ForegroundColor Red
        exit 1
    }

    # 3) 무결성 검증 태스크 생성 (매일 새벽 03:07)
    Write-Host "3. Creating VELOS Snapshot Integrity task..." -ForegroundColor Yellow

    $verify_command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"& '$PY' '$ROOT\scripts\verify_snapshots.py' --max 50`""

    Write-Host "   Command: $verify_command" -ForegroundColor Cyan

    schtasks /create /tn "VELOS Snapshot Integrity" /sc daily /st 03:07 `
        /ru SYSTEM /rl HIGHEST `
        /tr $verify_command `
        /f

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ VELOS Snapshot Integrity task created successfully" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ Failed to create VELOS Snapshot Integrity task" -ForegroundColor Red
        exit 1
    }

    # 4) 생성된 태스크 확인
    Write-Host "4. Verifying created tasks..." -ForegroundColor Yellow

    $created_tasks = @("VELOS Snapshot Catalog", "VELOS Snapshot Integrity")

    foreach ($task_name in $created_tasks) {
        $task_info = schtasks /query /tn $task_name /fo csv 2>$null
        if ($LASTEXITCODE -eq 0) {
            $task_data = $task_info | ConvertFrom-Csv
            $next_run = $task_data."Next Run Time"
            $status = $task_data."Status"

            Write-Host "   ✅ $task_name" -ForegroundColor Green
            Write-Host "      Next Run: $next_run" -ForegroundColor Cyan
            Write-Host "      Status: $status" -ForegroundColor Cyan
        }
        else {
            Write-Host "   ❌ Task not found: $task_name" -ForegroundColor Red
        }
    }

    # 5) 스크립트 파일 존재 확인
    Write-Host "5. Verifying script files..." -ForegroundColor Yellow

    $script_files = @(
        "$ROOT\scripts\snapshot_catalog.py",
        "$ROOT\scripts\verify_snapshots.py"
    )

    foreach ($script_file in $script_files) {
        if (Test-Path $script_file) {
            Write-Host "   ✅ Script exists: $script_file" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ Script missing: $script_file" -ForegroundColor Red
        }
    }

    Write-Host "[VELOS] ✅ Snapshot schedule tasks created successfully" -ForegroundColor Green
    Write-Host "   - VELOS Snapshot Catalog: Daily at 03:03" -ForegroundColor Cyan
    Write-Host "   - VELOS Snapshot Integrity: Daily at 03:07" -ForegroundColor Cyan

}
catch {
    Write-Host "[VELOS] Error creating snapshot tasks: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
