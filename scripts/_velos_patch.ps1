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
function VELOS-EnsureDir {
    param([Parameter(Mandatory=$true)][string]$Path)
    $dir = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
function VELOS-WriteAtomic {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Content)
    VELOS-EnsureDir -Path $Path
    $ts = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $backup = "$Path.$ts.bak"; $temp = "$Path.$ts.tmp"
    if (Test-Path $Path) { Copy-Item $Path $backup -Force }
    $utf8NoBOM = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($temp, $Content, $utf8NoBOM)
    Move-Item -Path $temp -Destination $Path -Force
    $fi = Get-Item $Path; $len = $fi.Length
    $sha = (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    if ($len -le 0) { throw "파일 크기가 0바이트입니다: $Path" }
    $bk = $null; if (Test-Path $backup) { $bk = $backup }
    return [PSCustomObject]@{ Path=$Path; Bytes=$len; SHA256=$sha; Backup=$bk }
}
function VELOS-SelfTest {
    param([Parameter(Mandatory=$true)][string]$Path)
    $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    switch ($ext) {
        ".py"   { & python -m py_compile $Path 2>$null; if ($LASTEXITCODE -ne 0) { throw "Python 컴파일 실패: $Path" } }
        ".ps1"  { try { [void][System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$null,[ref]$null) } catch { throw "PowerShell 파싱 실패: $Path" } }
        ".json" { try { Get-Content -Raw $Path | ConvertFrom-Json | Out-Null } catch { throw "JSON 파싱 실패: $Path" } }
        ".yml"  { try { if (Get-Module -ListAvailable -Name powershell-yaml) { Import-Module powershell-yaml -ErrorAction Stop; (Get-Content -Raw $Path | ConvertFrom-Yaml) | Out-Null } } catch { throw "YAML 파싱 실패: $Path" } }
        ".yaml" { try { if (Get-Module -ListAvailable -Name powershell-yaml) { Import-Module powershell-yaml -ErrorAction Stop; (Get-Content -Raw $Path | ConvertFrom-Yaml) | Out-Null } } catch { throw "YAML 파싱 실패: $Path" } }
        default { }
    }
}
function VELOS-Log {
    param([Parameter(Mandatory=$true)][hashtable]$Record,[string]$LogPath=$(Join-Path (Join-Path $env:VELOS_ROOT "data\logs") "ops_patch_log.jsonl"))
    VELOS-EnsureDir -Path $LogPath
    $json = ($Record | ConvertTo-Json -Depth 6 -Compress)
    Add-Content -Path $LogPath -Value $json
}
function VELOS-Patch {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Content,[string]$Run="",[switch]$DryRun)
    $record = @{ timestamp=(Get-Date).ToString("s"); path=$Path; action="patch"; result="pending"; size=$null; sha256=$null; backup=$null; run=$Run }
    if ($DryRun) { $record.result="dryrun"; VELOS-Log -Record $record; return $record }
    $w = VELOS-WriteAtomic -Path $Path -Content $Content
    $record.size=$w.Bytes; $record.sha256=$w.SHA256; $record.backup=$w.Backup
    VELOS-SelfTest -Path $Path
    if ($Run -and ([IO.Path]::GetExtension($Path).ToLowerInvariant() -eq ".py")) { & cmd /c $Run; if ($LASTEXITCODE -ne 0) { throw "Run 커맨드 실패: $Run" } }
    $record.result="ok"; VELOS-Log -Record $record; return $record
}
