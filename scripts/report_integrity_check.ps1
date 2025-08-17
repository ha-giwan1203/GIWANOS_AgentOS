# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference = "Stop"
$ROOT = $env:VELOS_ROOT; if(-not $ROOT){ $ROOT = "C:\giwanos" }

function Fail($m){ Write-Host "[FAIL] $m"; exit 1 }
function Ok($m){ Write-Host "[OK] $m" }

# 필수 리포트들
$repRisk   = Join-Path $ROOT "data\reports\file_usage_risk_report.json"
$repMani   = Join-Path $ROOT "data\reports\manifest_sync_report.json"
$repRefl   = Join-Path $ROOT "data\reports\reflection_risk_report.json"
$memClean  = Join-Path $ROOT "data\memory\learning_memory_cleaned.jsonl"

# 존재 확인
if(-not (Test-Path $repRisk)){ Fail "risk report missing" }
if(-not (Test-Path $repMani)){ Fail "manifest sync report missing" }
if(-not (Test-Path $repRefl)){ Fail "reflection risk report missing" }

# 형식 확인
try { $risk = Get-Content $repRisk -Raw | ConvertFrom-Json } catch { Fail "risk report malformed" }
try { $mani = Get-Content $repMani -Raw | ConvertFrom-Json } catch { Fail "manifest report malformed" }
try { $refl = Get-Content $repRefl -Raw | ConvertFrom-Json } catch { Fail "reflection report malformed" }

if(-not $risk.summary){ Fail "risk report missing summary" }
if(-not $mani.generated_at){ Fail "manifest report missing generated_at" }
if(-not $refl.counts){ Fail "reflection report missing counts" }

# 메모리 클린 파일은 존재만 확인(없어도 실패는 아님)
if(Test-Path $memClean){ Ok "memory cleaned present ($(Get-Item $memClean).Length bytes)" } else { Write-Host "[WARN] memory cleaned not present (tolerated)" }

Ok ("reports ok: orphan_candidate={0}, refl_high={1}" -f ([int]$risk.summary.ORPHAN_CANDIDATE,[int]$refl.counts.HIGH))
