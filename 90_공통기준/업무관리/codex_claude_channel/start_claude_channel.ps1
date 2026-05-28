$ErrorActionPreference = 'Stop'

$channelDir = $PSScriptRoot
$workspace = Resolve-Path (Join-Path $channelDir '..\..\..')
$mcpConfig = Join-Path $channelDir '.mcp.json'
$localTmp = Join-Path $channelDir '.tmp'

New-Item -Path $localTmp -ItemType Directory -Force | Out-Null

$env:CODEX_BRIDGE_PORT = '8791'
$env:CODEX_WORKSPACE = $workspace.Path
$env:TEMP = $localTmp
$env:TMP = $localTmp

Push-Location $workspace
try {
  claude --mcp-config $mcpConfig --dangerously-load-development-channels server:codex-bridge
}
finally {
  Pop-Location
}
