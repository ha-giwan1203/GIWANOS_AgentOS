# VELOS Environment Setup Script
# This script sets up environment variables for VELOS

param(
    [string]$Mode = "dev",
    [string]$Root = "C:/giwanos"
)

Write-Host "Setting up VELOS environment variables..." -ForegroundColor Green

# Set environment variables
$env:VELOS_ROOT = $Root
$env:VELOS_MODE = $Mode
$env:VELOS_REPORT_DIR = "$Root/data/reports"
$env:EMAIL_ENABLED = "0"

# Optional: Set API keys if they exist in configs
$configPath = "$Root/configs"
if (Test-Path "$configPath/.env") {
    Write-Host "Loading API keys from configs/.env..." -ForegroundColor Yellow
    Get-Content "$configPath/.env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
            Write-Host "  Set $key" -ForegroundColor Gray
        }
    }
}

# Verify environment setup
Write-Host "`nEnvironment variables set:" -ForegroundColor Green
Write-Host "  VELOS_ROOT: $env:VELOS_ROOT" -ForegroundColor Cyan
Write-Host "  VELOS_MODE: $env:VELOS_MODE" -ForegroundColor Cyan
Write-Host "  VELOS_REPORT_DIR: $env:VELOS_REPORT_DIR" -ForegroundColor Cyan
Write-Host "  EMAIL_ENABLED: $env:EMAIL_ENABLED" -ForegroundColor Cyan

# Check if required directories exist
$requiredDirs = @(
    "$Root/data",
    "$Root/data/reports",
    "$Root/data/memory",
    "$Root/logs"
)

Write-Host "`nChecking required directories..." -ForegroundColor Green
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dir (will be created)" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "`nVELOS environment setup complete!" -ForegroundColor Green
Write-Host "To make these changes permanent, add them to your PowerShell profile." -ForegroundColor Yellow
