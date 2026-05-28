param(
  [string]$TitleLike,
  [string]$Message,
  [switch]$Submit,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class CodexWin32 {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

  [DllImport("user32.dll")]
  public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

  [DllImport("user32.dll")]
  public static extern bool IsWindowVisible(IntPtr hWnd);

  [DllImport("user32.dll", CharSet = CharSet.Unicode)]
  public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

  [DllImport("user32.dll")]
  public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int processId);

  [DllImport("user32.dll")]
  public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

  [DllImport("user32.dll")]
  public static extern bool SetForegroundWindow(IntPtr hWnd);

  [DllImport("user32.dll")]
  public static extern IntPtr GetForegroundWindow();
}
"@

function Get-VisibleWindows {
  $windows = New-Object System.Collections.Generic.List[object]
  $callback = [CodexWin32+EnumWindowsProc]{
    param([IntPtr]$hWnd, [IntPtr]$lParam)

    if (-not [CodexWin32]::IsWindowVisible($hWnd)) {
      return $true
    }

    $titleBuffer = New-Object System.Text.StringBuilder 512
    [void][CodexWin32]::GetWindowText($hWnd, $titleBuffer, $titleBuffer.Capacity)
    $title = $titleBuffer.ToString()
    if ([string]::IsNullOrWhiteSpace($title)) {
      return $true
    }

    $processId = 0
    [void][CodexWin32]::GetWindowThreadProcessId($hWnd, [ref]$processId)
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
      return $true
    }

    $windows.Add([pscustomobject]@{
      Hwnd = $hWnd
      HwndHex = ('0x{0:X}' -f $hWnd.ToInt64())
      ProcessId = $processId
      ProcessName = $process.ProcessName
      Title = $title
    }) | Out-Null
    return $true
  }

  [void][CodexWin32]::EnumWindows($callback, [IntPtr]::Zero)
  return $windows
}

$windows = Get-VisibleWindows
$targets = $windows | Where-Object { $_.ProcessName -eq 'WindowsTerminal' }

if ($TitleLike) {
  $targets = $targets | Where-Object { $_.Title -like $TitleLike }
}

$targets = @($targets)

if ($DryRun) {
  $targets | Select-Object HwndHex, ProcessId, ProcessName, Title | ConvertTo-Json -Depth 3
  exit 0
}

if ($targets.Count -eq 0) {
  Write-Error "target_not_found: WindowsTerminal title filter '$TitleLike'"
}

if ($targets.Count -gt 1) {
  $list = ($targets | ForEach-Object { "$($_.HwndHex) pid=$($_.ProcessId) title=$($_.Title)" }) -join "`n"
  Write-Error "target_not_unique: pass -TitleLike. candidates:`n$list"
}

if ([string]::IsNullOrWhiteSpace($Message)) {
  Write-Error 'message_required'
}

$target = $targets[0]
[void][CodexWin32]::ShowWindow($target.Hwnd, 9)
Start-Sleep -Milliseconds 150
[void][CodexWin32]::SetForegroundWindow($target.Hwnd)
Start-Sleep -Milliseconds 350

$foreground = [CodexWin32]::GetForegroundWindow()
if ($foreground -ne $target.Hwnd) {
  Write-Error ("foreground_lock: expected={0} actual=0x{1:X}" -f $target.HwndHex, $foreground.ToInt64())
}

$oldClipboard = $null
try {
  $oldClipboard = Get-Clipboard -Raw -ErrorAction SilentlyContinue
} catch {
  $oldClipboard = $null
}

Set-Clipboard -Value $Message
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 120

if ($Submit) {
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
}

Start-Sleep -Milliseconds 120
if ($null -ne $oldClipboard) {
  Set-Clipboard -Value $oldClipboard
}

[pscustomobject]@{
  status = 'SENT'
  submitted = [bool]$Submit
  hwnd = $target.HwndHex
  process_id = $target.ProcessId
  title = $target.Title
} | ConvertTo-Json -Depth 3
