param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$CommandParts
)

$bashCandidates = @(
    'C:\Program Files\Git\bin\bash.exe',
    'C:\Program Files\Git\usr\bin\bash.exe'
)

$bashPath = $bashCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $bashPath) {
    Write-Error "Git Bash 실행 파일을 찾지 못했습니다. 확인 경로: $($bashCandidates -join ', ')"
    exit 1
}

$command = ($CommandParts -join ' ').Trim()
if (-not $command) {
    Write-Error "실행할 Bash 명령이 비어 있습니다."
    exit 1
}

& $bashPath -lc $command
exit $LASTEXITCODE
