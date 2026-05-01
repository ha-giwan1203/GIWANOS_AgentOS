# probe_mesclient_network.ps1
# Phase A pre-check: identify mesclient.exe network endpoints (read-only).
#
# Purpose: before installing capture tools, observe which host:port mesclient.exe talks to via OS-level APIs.
# Output: console + state/probe_<timestamp>.txt
# Safety: no traffic interception. Only netstat / Get-NetTCPConnection.
# Note: ASCII-only messages to avoid PS 5.1 cp949/utf-8 mismatch.

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $PSScriptRoot "..\state"
$outFile = Join-Path $outDir "probe_$timestamp.txt"

function Write-Both {
    param([string]$msg)
    Write-Host $msg
    Add-Content -Path $outFile -Value $msg -Encoding UTF8
}

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

Write-Both "=== mesclient.exe network probe ($timestamp) ==="
Write-Both ""

$procs = Get-Process -Name "mesclient" -ErrorAction SilentlyContinue
if (-not $procs) {
    Write-Both "[FAIL] mesclient.exe not running. Open jobsetup screen, then re-run."
    Write-Both ""
    Write-Both "Candidate SmartMES-related processes (for reference):"
    $cands = Get-Process | Where-Object { $_.ProcessName -match "mes|smart" } | Select-Object Id, ProcessName, Path
    if ($cands) {
        $cands | Format-Table -AutoSize | Out-String | ForEach-Object { Write-Both $_ }
    } else {
        Write-Both "  (none found)"
    }
    Write-Both ""
    Write-Both "Result saved: $outFile"
    exit 1
}

Write-Both "[OK] mesclient.exe found:"
$procs | Select-Object Id, ProcessName, @{N="Path";E={$_.Path}}, StartTime |
    Format-Table -AutoSize | Out-String | ForEach-Object { Write-Both $_ }

foreach ($p in $procs) {
    Write-Both ""
    Write-Both "--- PID $($p.Id) TCP connections ---"
    $conns = Get-NetTCPConnection -OwningProcess $p.Id -ErrorAction SilentlyContinue
    if (-not $conns) {
        Write-Both "  (no connections - UDP only or already closed)"
        continue
    }
    $conns | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State |
        Sort-Object RemoteAddress, RemotePort |
        Format-Table -AutoSize | Out-String | ForEach-Object { Write-Both $_ }

    Write-Both ""
    Write-Both "--- Established remote endpoints (nslookup) ---"
    $remotes = $conns | Where-Object { $_.State -eq "Established" -and $_.RemoteAddress -notmatch "^(0\.0\.0\.0|127\.|::)" } |
               Select-Object -ExpandProperty RemoteAddress -Unique
    foreach ($r in $remotes) {
        try {
            $dns = [System.Net.Dns]::GetHostEntry($r)
            Write-Both "  $r -> $($dns.HostName)"
        } catch {
            Write-Both "  $r -> (reverse lookup failed)"
        }
    }
}

Write-Both ""
Write-Both "--- UDP listeners (reference) ---"
foreach ($p in $procs) {
    $udp = Get-NetUDPEndpoint -OwningProcess $p.Id -ErrorAction SilentlyContinue |
           Select-Object LocalAddress, LocalPort
    if ($udp) {
        $udp | Format-Table -AutoSize | Out-String | ForEach-Object { Write-Both $_ }
    } else {
        Write-Both "  (none)"
    }
}

Write-Both ""
Write-Both "=== Result saved: $outFile ==="
Write-Both ""
Write-Both "Next steps:"
Write-Both "  1) Record Established RemoteAddress:RemotePort into traffic_capture_20260501.md '1-3' section"
Write-Both "  2) Configure Wireshark/Fiddler filter for that host:port"
Write-Both "  3) Run jobsetup dry-run once while capturing"
