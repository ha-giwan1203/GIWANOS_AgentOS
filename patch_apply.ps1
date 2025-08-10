param(
  [string]$PlanPath = ".\patch_plan.csv",
  [switch]$DryRun,
  [switch]$NoImportInject
)

function Escape-Regex([string]$s){ [regex]::Escape($s) }

if (!(Test-Path $PlanPath)) { throw "Plan CSV not found: $PlanPath" }
$plan = Import-Csv $PlanPath
$backupRoot = ".\.patch_backups\" + (Get-Date -Format "yyyyMMdd_HHmmss")
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

foreach ($row in $plan) {
  $file = $row.File
  if (-not (Test-Path $file)) { Write-Warning "파일 없음: $file"; continue }

  $ext = [IO.Path]::GetExtension($file).ToLower()
  $find = $row.Find
  $replPy  = $row.ReplacePy
  $replCmd = $row.ReplaceCMD
  $replPs1 = $row.ReplacePS1
  $import  = $row.ImportLine

  $content = Get-Content -Raw -LiteralPath $file -ErrorAction Stop

  switch ($ext) {
    ".py"  { $replace = $replPy }
    ".cmd" { $replace = $replCmd }
    ".bat" { $replace = $replCmd }
    ".ps1" { $replace = $replPs1 }
    default { $replace = $replPy }
  }

  $escaped = Escape-Regex $find
  $matches = [regex]::Matches($content, $escaped)
  if ($matches.Count -eq 0) { continue }

  if ($DryRun) {
    Write-Host "DRYRUN: $file  ($($matches.Count) hit)  '$find' -> '$replace'"
    continue
  }

  $rel = $file -replace "[:\\\/]", "_"
  $bk = Join-Path $backupRoot $rel
  Copy-Item -LiteralPath $file -Destination $bk -Force

  $new = [regex]::Replace($content, $escaped, [Text.RegularExpressions.MatchEvaluator]{ param($m) $replace })

  if ($ext -eq ".py" -and -not $NoImportInject) {
    if ($import -and ($new -notmatch [regex]::Escape($import))) {
      $lines = $new -split "`r?`n"
      $idx = 0
      while ($idx -lt $lines.Length -and ($lines[$idx] -match '^(#!|#.*coding[:=])' -or $lines[$idx] -match '^\s*#')) { $idx++ }
      $lines = $lines[0..($idx-1)] + $import + $lines[$idx..($lines.Length-1)]
      $new = ($lines -join "`r`n")
    }
  }

  Set-Content -LiteralPath $file -Value $new -Encoding UTF8
  Write-Host "PATCHED: $file  ($($matches.Count) repl)  backup=$bk"
}

Write-Host "완료. 백업 폴더: $backupRoot"
