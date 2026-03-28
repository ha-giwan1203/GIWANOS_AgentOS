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
