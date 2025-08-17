# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

$ErrorActionPreference="Stop"
$ROOT=$env:VELOS_ROOT; if(-not $ROOT){$ROOT="C:\giwanos"}
$base=Join-Path $ROOT "data\quarantine"
$backup_dir=Join-Path $ROOT "data\backups"
$cut=(Get-Date).AddDays(-14)

Write-Host "[VELOS] Quarantine 정리 시작 - $ROOT"
Write-Host "[VELOS] 격리 디렉토리: $base"
Write-Host "[VELOS] 백업 디렉토리: $backup_dir"
Write-Host "[VELOS] 정리 기준: $cut (14일 전)"

# 격리 디렉토리 확인
if(-not (Test-Path $base)){
    Write-Host "[VELOS] 격리 디렉토리가 없습니다: $base"
    exit 0
}

# 백업 디렉토리 생성
New-Item -ItemType Directory -Force -Path $backup_dir | Out-Null

# 14일 이상 된 격리 디렉토리들 찾기
$old_dirs = Get-ChildItem $base -Directory | Where-Object { $_.LastWriteTime -lt $cut }
Write-Host "[VELOS] 정리 대상: $($old_dirs.Count)개 디렉토리"

if($old_dirs.Count -eq 0){
    Write-Host "[VELOS] 정리할 디렉토리가 없습니다"
    exit 0
}

# 정리 실행
$purged_count = 0
$error_count = 0

foreach($dir in $old_dirs){
    try {
        $zip = Join-Path $backup_dir ("purged_orphans_{0}.zip" -f $dir.Name)

        # 기존 ZIP 파일이 있으면 삭제
        if(Test-Path $zip){
            Remove-Item $zip -Force
            Write-Host "[CLEAN] 기존 ZIP 삭제: $zip"
        }

        # ZIP 압축 생성
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::CreateFromDirectory($dir.FullName, $zip)

        # 원본 디렉토리 삭제
        Remove-Item $dir.FullName -Recurse -Force

        Write-Host "[PURGED] $($dir.FullName) -> $zip"
        $purged_count++

    } catch {
        Write-Host "[ERR] $($dir.FullName) 정리 실패: $_"
        $error_count++
    }
}

# 정리 완료 요약
$summary = @{
    total_old_dirs = $old_dirs.Count
    purged_success = $purged_count
    errors = $error_count
    cutoff_date = $cut.ToString("yyyy-MM-dd HH:mm:ss")
    completed_at = Get-Date -Format s
} | ConvertTo-Json -Compress

$summary | Out-File -Encoding utf8 (Join-Path $backup_dir "purge_summary.json")

Write-Host "[OK] Quarantine 정리 완료"
Write-Host "[SUMMARY] 총 $($old_dirs.Count)개 중 $purged_count개 정리, $error_count개 오류"
Write-Host "[BACKUP] $backup_dir"
Write-Host "[SUMMARY] $(Join-Path $backup_dir "purge_summary.json")"
