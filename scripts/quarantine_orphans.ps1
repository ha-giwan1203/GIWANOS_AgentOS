# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference="Stop"
$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}
$rep=Join-Path $ROOT "data\reports\file_usage_risk_report.json"
$qdir=Join-Path $ROOT "data\quarantine\$(Get-Date -Format yyyyMMdd_HHmmss)"
$log = Join-Path $qdir "quarantine_log.jsonl"

Write-Host "[VELOS] Quarantine 시작 - $ROOT"
Write-Host "[VELOS] 리포트: $rep"
Write-Host "[VELOS] 격리 디렉토리: $qdir"

# 격리 디렉토리 생성
New-Item -ItemType Directory -Force -Path $qdir | Out-Null

# 리포트 파일 확인
if(-not (Test-Path $rep)){
    Write-Host "[ERR] 리스크 리포트가 없습니다: $rep"
    exit 1
}

# JSON 로드
try {
    $json = Get-Content $rep -Raw | ConvertFrom-Json
    Write-Host "[VELOS] 리포트 로드 완료"
} catch {
    Write-Host "[ERR] JSON 파싱 실패: $_"
    exit 1
}

# QUARANTINE_CANDIDATE 파일들 추출
$files = $json.files.GetEnumerator() | Where-Object { $_.Value.label -eq "QUARANTINE_CANDIDATE" } | % { $_.Key }
Write-Host "[VELOS] 격리 대상: $($files.Count)개 파일"

if($files.Count -eq 0){
    Write-Host "[VELOS] 격리 대상 파일이 없습니다"
    exit 0
}

# 파일 격리 실행
$moved_count = 0
$error_count = 0

foreach($rel in $files){
    $src = Join-Path $ROOT $rel
    if(Test-Path $src){
        try {
            $dst = Join-Path $qdir $rel
            New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
            $hash = (Get-FileHash $src -Algorithm SHA256).Hash
            Move-Item -Force $src $dst

            # 격리 로그 기록
            $log_entry = @{
                rel = $rel
                from = $src
                to = $dst
                sha256 = $hash
                ts = Get-Date -Format s
            } | ConvertTo-Json -Compress

            $log_entry | Out-File -Append -Encoding utf8 $log
            Write-Host "[MOVE] $rel -> $dst"
            $moved_count++
        } catch {
            Write-Host "[ERR] $rel 이동 실패: $_"
            $error_count++
        }
    } else {
        Write-Host "[MISS] $rel (파일 없음)"
    }
}

# 격리 완료 요약
$summary = @{
    total_candidates = $files.Count
    moved_success = $moved_count
    errors = $error_count
    quarantine_dir = $qdir
    log_file = $log
    completed_at = Get-Date -Format s
} | ConvertTo-Json -Compress

$summary | Out-File -Encoding utf8 (Join-Path $qdir "quarantine_summary.json")

Write-Host "[OK] Quarantine 완료 -> $qdir"
Write-Host "[SUMMARY] 총 $($files.Count)개 중 $moved_count개 이동, $error_count개 오류"
Write-Host "[LOG] $log"
Write-Host "[SUMMARY] $(Join-Path $qdir "quarantine_summary.json")"
