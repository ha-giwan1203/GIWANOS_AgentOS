# UTF-8
$root = "C:\giwanos\data\logs"
$days = 90

Get-ChildItem $root -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$days) } |
    ForEach-Object {
        Compress-Archive -Path $_.FullName -DestinationPath "$($_.FullName).zip" -Force
        Remove-Item $_.FullName -Force
    }

Write-Host "로그 로테이션 완료($days일 이전 → zip 압축)."
