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

[CmdletBinding()]
param(
    [string]$Root = "C:\giwanos",
    [string]$OutputFile = "C:\giwanos\data\reports\velos_checklist_report.md"
)

$ErrorActionPreference = "Stop"
$PSDefaultParameterValues["Out-File:Encoding"] = "utf8"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Good($m) { Write-Host "✅ $m" -ForegroundColor Green }
function Warn($m) { Write-Host "⚠️  $m" -ForegroundColor Yellow }
function Bad($m) { Write-Host "❌ $m" -ForegroundColor Red }

# 경로 설정
$Venv = Join-Path $Root ".venv_link"
$Py = Join-Path $Venv "Scripts\python.exe"
$Health = Join-Path $Root "data\logs\system_health.json"

# 헬퍼 함수
function Read-Json($p) {
    try {
        Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        $null
    }
}

function Test-PythonModule($module) {
    try {
        $result = & $Py -c "import $module; print('OK')" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# 체크리스트 실행
Write-Host "=== VELOS 체크리스트 실행 ===" -ForegroundColor Magenta

$checklist = @{
    "메모리 DB 적재"         = $false
    "JSON ↔ SQLite 동기화" = $false
    "자동 보고서 전송"         = $false
    "스케줄러 확인"           = $false
    "VELOS 마스터 루프"      = $false
    "스냅샷 검증"            = $false
    "컨텍스트 블록 점검"        = $false
    "375자 제한 확인"        = $false
}

$details = @{}

# 1. 메모리 DB 적재 확인
Info "1. 메모리 DB 적재 확인..."
try {
    $result = & $Py -c "from memory_adapter import MemoryAdapter; m = MemoryAdapter(); stats = m.get_stats(); print('DB records:', stats.get('db_records', 0))" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $db_records = ($result | Select-String "DB records: (\d+)").Matches.Groups[1].Value
        if ([int]$db_records -gt 0) {
            $checklist["메모리 DB 적재"] = $true
            Good "메모리 DB 적재: $db_records records"
            $details["메모리 DB 적재"] = "DB records: $db_records"
        }
        else {
            Warn "메모리 DB 적재: 0 records"
            $details["메모리 DB 적재"] = "DB records: 0 (empty)"
        }
    }
    else {
        Bad "메모리 DB 적재 확인 실패"
        $details["메모리 DB 적재"] = "확인 실패"
    }
}
catch {
    Bad "메모리 DB 적재 확인 오류: $($_.Exception.Message)"
    $details["메모리 DB 적재"] = "오류: $($_.Exception.Message)"
}

# 2. JSON ↔ SQLite 동기화 확인
Info "2. JSON ↔ SQLite 동기화 확인..."
try {
    $result = & $Py -c "from memory_adapter import MemoryAdapter; m = MemoryAdapter(); moved = m.flush_jsonl_to_db(); print('Flushed:', moved)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $checklist["JSON ↔ SQLite 동기화"] = $true
        Good "JSON ↔ SQLite 동기화: 정상"
        $details["JSON ↔ SQLite 동기화"] = "동기화 정상"
    }
    else {
        Bad "JSON ↔ SQLite 동기화 실패"
        $details["JSON ↔ SQLite 동기화"] = "동기화 실패"
    }
}
catch {
    Bad "JSON ↔ SQLite 동기화 확인 오류: $($_.Exception.Message)"
    $details["JSON ↔ SQLite 동기화"] = "오류: $($_.Exception.Message)"
}

# 3. 자동 보고서 전송 확인
Info "3. 자동 보고서 전송 확인..."
$report_modules = @("slack", "notion", "email", "pushbullet")
$report_working = 0
foreach ($module in $report_modules) {
    if (Test-PythonModule $module) {
        $report_working++
    }
}
if ($report_working -gt 0) {
    $checklist["자동 보고서 전송"] = $true
    Good "자동 보고서 전송: $report_working/$($report_modules.Count) 모듈 사용 가능"
    $details["자동 보고서 전송"] = "사용 가능 모듈: $report_working/$($report_modules.Count)"
}
else {
    Warn "자동 보고서 전송: 모듈 없음"
    $details["자동 보고서 전송"] = "사용 가능한 모듈 없음"
}

# 4. 스케줄러 확인
Info "4. 스케줄러 확인..."
$velos_tasks = schtasks /query /fo csv 2>$null | Select-String "VELOS"
if ($velos_tasks) {
    $task_count = ($velos_tasks | Measure-Object).Count
    $checklist["스케줄러 확인"] = $true
    Good "스케줄러 확인: $task_count VELOS 태스크 발견"
    $details["스케줄러 확인"] = "VELOS 태스크: $task_count개"
}
else {
    Bad "스케줄러 확인: VELOS 태스크 없음"
    $details["스케줄러 확인"] = "VELOS 태스크 없음"
}

# 5. VELOS 마스터 루프 확인
Info "5. VELOS 마스터 루프 확인..."
$master_loop_task = schtasks /query /fo csv 2>$null | Select-String "VELOS-MasterLoop"
if ($master_loop_task) {
    $checklist["VELOS 마스터 루프"] = $true
    Good "VELOS 마스터 루프: 태스크 존재"
    $details["VELOS 마스터 루프"] = "태스크 존재"
}
else {
    Warn "VELOS 마스터 루프: 태스크 없음"
    $details["VELOS 마스터 루프"] = "태스크 없음"
}

# 6. 스냅샷 검증 확인
Info "6. 스냅샷 검증 확인..."
$health = Read-Json $Health
if ($health.snapshot_verify_ok) {
    $checklist["스냅샷 검증"] = $true
    Good "스냅샷 검증: 정상"
    $details["스냅샷 검증"] = "검증 정상"
}
else {
    Bad "스냅샷 검증: 실패"
    $details["스냅샷 검증"] = "검증 실패"
}

# 7. 컨텍스트 블록 점검
Info "7. 컨텍스트 블록 점검..."
try {
    $result = & $Py -c "from modules.core.context_builder import build_context_block; ctx = build_context_block(limit=10, hours=24); print('Context length:', len(ctx))" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ctx_length = ($result | Select-String "Context length: (\d+)").Matches.Groups[1].Value
        $checklist["컨텍스트 블록 점검"] = $true
        Good "컨텍스트 블록 점검: $ctx_length chars"
        $details["컨텍스트 블록 점검"] = "길이: $ctx_length chars"
    }
    else {
        Bad "컨텍스트 블록 점검 실패"
        $details["컨텍스트 블록 점검"] = "점검 실패"
    }
}
catch {
    Bad "컨텍스트 블록 점검 오류: $($_.Exception.Message)"
    $details["컨텍스트 블록 점검"] = "오류: $($_.Exception.Message)"
}

# 8. 375자 제한 확인
Info "8. 375자 제한 확인..."
try {
    $result = & $Py -c "from modules.core.context_builder import build_context_block; ctx = build_context_block(limit=10, hours=24); print('Length:', len(ctx)); print('OK' if len(ctx) <= 375 else 'TOO_LONG')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $length_ok = $result | Select-String "OK"
        if ($length_ok) {
            $checklist["375자 제한 확인"] = $true
            Good "375자 제한 확인: 통과"
            $details["375자 제한 확인"] = "375자 이하 통과"
        }
        else {
            Warn "375자 제한 확인: 초과"
            $details["375자 제한 확인"] = "375자 초과"
        }
    }
    else {
        Bad "375자 제한 확인 실패"
        $details["375자 제한 확인"] = "확인 실패"
    }
}
catch {
    Bad "375자 제한 확인 오류: $($_.Exception.Message)"
    $details["375자 제한 확인"] = "오류: $($_.Exception.Message)"
}

# 결과 요약
Write-Host ""
Write-Host "=== VELOS 체크리스트 결과 ===" -ForegroundColor Magenta
$passed = ($checklist.Values | Where-Object { $_ -eq $true }).Count
$total = $checklist.Count
Write-Host "통과: $passed/$total" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

foreach ($item in $checklist.Keys) {
    $status = if ($checklist[$item]) { "✅" } else { "❌" }
    $detail = $details[$item]
    Write-Host "$status $item`: $detail"
}

# 보고서 생성
$report_content = @"
# VELOS 체크리스트 보고서

생성일시: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## 체크리스트 결과

통과: $passed/$total

"@

foreach ($item in $checklist.Keys) {
    $status = if ($checklist[$item]) { "✅" } else { "❌" }
    $detail = $details[$item]
    $report_content += "`n$status **$item`**`n- $detail`n"
}

$report_content += @"

## 시스템 상태

- Python 경로: $Py
- 가상환경: $Venv
- 헬스 로그: $Health

## 권장사항

"@

if ($passed -lt $total) {
    $report_content += "`n- 일부 체크리스트 항목이 실패했습니다.`n- 시스템 상태를 점검하고 필요한 조치를 취하세요.`n"
}
else {
    $report_content += "`n- 모든 체크리스트 항목이 통과했습니다.`n- VELOS 시스템이 정상적으로 작동하고 있습니다.`n"
}

# 보고서 저장
New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($OutputFile)) | Out-Null
$report_content | Out-File $OutputFile -Encoding utf8
Good "체크리스트 보고서 저장: $OutputFile"

Write-Host ""
Write-Host "=== 체크리스트 완료 ===" -ForegroundColor Magenta
if ($passed -eq $total) {
    Good "모든 체크리스트 통과!"
    exit 0
}
else {
    Warn "일부 체크리스트 실패 ($passed/$total)"
    exit 1
}
