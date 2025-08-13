param([switch]$Once)

$pwsh = "C:\Program Files\PowerShell\7\pwsh.exe"
$ps   = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Run-PowerShellFile([string]$file,[string[]]$args) {
    if (Test-Path $pwsh) {
        & $pwsh -NoProfile -ExecutionPolicy Bypass -File $file @args
    } else {
        & $ps   -NoProfile -ExecutionPolicy Bypass -File $file @args
    }
}

# 1. 메모리 헬스체크
$mw = "C:\giwanos\tools\memory_watch.ps1"
if (Test-Path $mw) { Run-PowerShellFile $mw @() }

# 2. CONTEXT_PACK 생성
$mk = "C:\giwanos\tools\make_context_pack.py"
if (Test-Path $mk) { python $mk }

# 3. 자동수정 워치
$af = "C:\giwanos\tools\autofix.ps1"
if (Test-Path $af) {
    if ($Once) {
        Run-PowerShellFile $af @('-Once:$true')
    } else {
        Run-PowerShellFile $af @()
    }
}
