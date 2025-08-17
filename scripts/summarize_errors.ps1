# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference="Stop"
$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}
$logs_dir=Join-Path $ROOT "data\logs"
$reports_dir=Join-Path $ROOT "data\reports"
$cutoff=(Get-Date).AddHours(-48)

Write-Host "[VELOS] 에러 요약 시작 - $ROOT"
Write-Host "[VELOS] 로그 디렉토리: $logs_dir"
Write-Host "[VELOS] 검색 기간: 최근 48시간 ($cutoff ~ 현재)"

# 로그 디렉토리 확인
if(-not (Test-Path $logs_dir)){
    Write-Host "[VELOS] 로그 디렉토리가 없습니다: $logs_dir"
    exit 0
}

# 최근 48시간 내 로그 파일들 찾기
$logs=Get-ChildItem $logs_dir -Recurse -Filter *.log | Where-Object { $_.LastWriteTime -gt $cutoff }
Write-Host "[VELOS] 검색 대상: $($logs.Count)개 로그 파일"

if($logs.Count -eq 0){
    Write-Host "[VELOS] 검색할 로그 파일이 없습니다"
    exit 0
}

# 에러 분석
$rows=@()
$total_errors = 0

foreach($f in $logs){
    try {
        $errs=(Select-String -Path $f.FullName -Pattern "ERROR|Traceback" -AllMatches).Line
        if($errs){
            $rel_path = $f.FullName.Replace($ROOT, "").TrimStart("\")
            $rows += [pscustomobject]@{
                file = $rel_path
                full_path = $f.FullName
                count = $errs.Count
                last_modified = $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                size_kb = [math]::Round($f.Length / 1KB, 2)
            }
            $total_errors += $errs.Count
            Write-Host "[FOUND] $rel_path: $($errs.Count)개 에러"
        }
    } catch {
        Write-Host "[ERR] $($f.FullName) 분석 실패: $_"
    }
}

# 보고서 디렉토리 생성
New-Item -ItemType Directory -Force -Path $reports_dir | Out-Null

# JSON 보고서 생성
$outj=Join-Path $reports_dir "error_summary.json"
$summary_data = @{
    generated_at = Get-Date -Format s
    search_period_hours = 48
    cutoff_time = $cutoff.ToString("yyyy-MM-dd HH:mm:ss")
    total_log_files = $logs.Count
    files_with_errors = $rows.Count
    total_errors = $total_errors
    error_details = $rows
} | ConvertTo-Json -Depth 3

$summary_data | Out-File -Encoding utf8 $outj

# 마크다운 보고서 생성
$outm=Join-Path $reports_dir "error_summary.md"
$md_content = @"
# VELOS Error Summary (최근 48시간)

- **생성 시간**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **검색 기간**: $($cutoff.ToString("yyyy-MM-dd HH:mm:ss")) ~ $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **검색된 로그 파일**: $($logs.Count)개
- **에러 발생 파일**: $($rows.Count)개
- **총 에러 수**: $total_errors개

## 에러 발생 파일 목록

"@

if($rows.Count -gt 0){
    $md_content += $rows | ForEach-Object {
        "- **$($_.file)** ($($_.last_modified)): $($_.count)개 에러 ($($_.size_kb)KB)"
    } -join "`n"
} else {
    $md_content += "- 에러가 발생한 파일이 없습니다"
}

$md_content += @"

## 상세 정보

각 파일의 전체 경로와 에러 수를 확인하려면 JSON 보고서를 참조하세요: `error_summary.json`
"@

$md_content | Out-File -Encoding utf8 $outm

Write-Host "[OK] 에러 요약 완료"
Write-Host "[SUMMARY] $($logs.Count)개 로그 파일 중 $($rows.Count)개에서 $total_errors개 에러 발견"
Write-Host "[JSON] $outj"
Write-Host "[MD] $outm"
