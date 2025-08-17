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
param(
  [string]$MemJson = "C:\giwanos\data\memory\learning_memory.json",
  [string]$ProbeTag = "[MWA_PROBE]"
)

$ErrorActionPreference = "Stop"

# 파일/폴더 보장
$dir = Split-Path $MemJson -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
if (-not (Test-Path $MemJson)) { New-Item -ItemType File -Force $MemJson | Out-Null }

$ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
$entry = @{ from="system"; insight="$ProbeTag heartbeat $ts"; ts=$ts } | ConvertTo-Json -Compress

# 쓰기
Add-Content -LiteralPath $MemJson -Value $entry

Start-Sleep -Milliseconds 200

# 읽기 검증
$hit = Select-String -Path $MemJson -Pattern $ProbeTag -SimpleMatch -ErrorAction SilentlyContinue
if (-not $hit) {
    Write-Host "❌ 메모리 쓰기/읽기 실패: $MemJson" -ForegroundColor Red
    exit 2
}
Write-Host "✅ 메모리 OK: $($hit.Count) entries (latest $ts)" -ForegroundColor Green
