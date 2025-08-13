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
