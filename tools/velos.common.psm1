function Get-VelosRoot {
  $root = $env:VELOS_ROOT; if (-not $root) { $root = "C:\giwanos" }
  return [IO.Path]::GetFullPath($root)
}

function Write-Utf8NoBom {
  param([string]$Path, [string]$Text)
  New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
  $enc = New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($Path, $Text, $enc)
}

function Ensure-Dirs {
  param([string[]]$Paths)
  foreach ($d in $Paths) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
  }
}
Set-Alias -Name Initialize-Dirs -Value Ensure-Dirs

function New-VelosLogger {
  param([string]$Name, [string]$LogPath)
  Ensure-Dirs -Paths @(Split-Path $LogPath -Parent)
  $logger = [pscustomobject]@{ Name = $Name; Path = $LogPath }
  $logger | Add-Member -MemberType ScriptMethod -Name Info -Value {
    param($m)
    $line = ("[{0}][INFO ][{1:s}] {2}" -f $this.Name, (Get-Date), $m)
    Add-Content -Path $this.Path -Value $line -Encoding UTF8
  }
  $logger | Add-Member -MemberType ScriptMethod -Name Warn -Value {
    param($m)
    $line = ("[{0}][WARN ][{1:s}] {2}" -f $this.Name, (Get-Date), $m)
    Add-Content -Path $this.Path -Value $line -Encoding UTF8
  }
  $logger | Add-Member -MemberType ScriptMethod -Name Error -Value {
    param($m)
    $line = ("[{0}][ERROR][{1:s}] {2}" -f $this.Name, (Get-Date), $m)
    Add-Content -Path $this.Path -Value $line -Encoding UTF8
  }
  return $logger
}