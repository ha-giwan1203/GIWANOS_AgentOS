
# C:\giwanos\patch_agents.ps1

# 1) 패키지 모듈 전체 경로
$pkg = 'C:\giwanos\giwanos_agent'

# 2) 절대 임포트로 변경: from .xxx → from giwanos_agent.xxx
Get-ChildItem $pkg -Filter '*.py' | ForEach-Object {
    (Get-Content $_.FullName) `
      -replace 'from \.([a-z_]+) import', 'from giwanos_agent.$1 import' |
    Set-Content  $_.FullName
}

# 3) subprocess.run 옵션 패치: text=True → encoding/ignore
$pattern     = 'capture_output=True,\s*text=True,\s*check=True'
$replacement = 'capture_output=True, encoding="utf-8", errors="ignore", check=True'
Get-ChildItem $pkg -Filter '*.py' | ForEach-Object {
    (Get-Content $_.FullName) `
      -replace $pattern, $replacement |
    Set-Content  $_.FullName
}

Write-Host "✅ giwanos_agent 패치 완료!"
