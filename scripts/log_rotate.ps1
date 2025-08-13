$DefaultRoot = if ($env:VELOS_ROOT) { $env:VELOS_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")) }
# === VELOS 운영 철학 선언문 ===
# 본 스크립트는 VELOS 시스템 자동화 구조에 따라 작성되었으며,
# 절대경로 하드코딩을 제거하고 환경변수/기본 루트를 통한 유연한 경로 설정을 지원합니다.
# 모든 변경 사항은 운영 철학(파일명 불변·검증 후 배포)에 맞춰 관리됩니다.

# 기본 루트 경로 설정
}

# 로그 디렉토리 경로

# 로테이션 대상 확장자
$extensions = @("*.log", "*.jsonl")

# 날짜 포맷
$dateStamp = Get-Date -Format "yyyyMMdd_HHmmss"

# 백업 디렉토리 생성
$backupDir = Join-Path $logDir "archive"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# 로테이션 처리
foreach ($ext in $extensions) {
    Get-ChildItem -Path $logDir -Filter $ext -File -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $dest = Join-Path $backupDir "$($_.BaseName)_$dateStamp$($_.Extension)"
            Move-Item -Path $_.FullName -Destination $dest -Force
            Write-Host "✅ 로테이션 완료: $($_.Name) → $(Split-Path $dest -Leaf)"
        }
        catch {
            Write-Host "⚠ 로테이션 실패: $($_.FullName) - $($_.Exception.Message)"
        }
    }
}

Write-Host "=== 로그 로테이션 완료 ==="
