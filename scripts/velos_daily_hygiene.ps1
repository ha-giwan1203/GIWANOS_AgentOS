# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS Daily Hygiene Pipeline (Hidden-friendly)
$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT="C:\giwanos" }

function Step($name, $block) {
  Write-Host "=== [$name] ==="
  & $block
  if ($LASTEXITCODE -ne 0) { throw "Step failed: $name" }
}

# 0) 환경
Write-Host "[env] ROOT=$ROOT"
$python = "python"

# 1) 트레이스 + 매니페 동기화
Step "trace+manifest sync" {
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\run_runtime_trace_and_sync.ps1")
}

# 2) 리스크 리포트 보장(없거나 낡으면 생성)
Step "ensure risk report" {
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\ensure_risk_report.ps1")
}

# 3) 파일 사용성 리스크 감사(최신으로 갱신)
Step "file usage risk audit" {
  & $python (Join-Path $ROOT "tools\analysis\file_usage_risk_audit.py")
}

# 4) orphan 격리(삭제 아님)
Step "quarantine orphans" {
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\quarantine_orphans.ps1")
}

# 5) 메모리 정리
Step "memory cleaner" {
  & $python (Join-Path $ROOT "modules\automation\memory_cleaner.py") --run-clean
}

# 6) 리플렉션 리스크 태깅
Step "reflection risk tagger" {
  & $python (Join-Path $ROOT "modules\automation\reflection_risk_tagger.py") --include-reflections
}

# 7) 리포트 무결성 점검
Step "report integrity" {
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\report_integrity_check.ps1")
}

# 8) 운영 종합 점검(여기서 orphan>0면 즉시 실패하도록 이미 설정됨)
Step "operational sanity" {
  powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ROOT "scripts\velos_operational_sanity.ps1")
}

# 9) 요약 리포트 생성
Step "daily summary" {
  & $python (Join-Path $ROOT "tools\analysis\hygiene_daily_summary.py")
}

Write-Host "[PASS] VELOS Daily Hygiene completed."
exit 0
