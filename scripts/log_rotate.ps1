$root = 'C:\giwanos\data\logs'
Get-ChildItem $root -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item -Force -ErrorAction SilentlyContinue


