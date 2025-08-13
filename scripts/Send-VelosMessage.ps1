function Send-VelosMessage {
    param(
        [Parameter(Mandatory=$true)][string]$Room,
        [Parameter(Mandatory=$true)][string]$Body,
        [string]$User = "local"
    )
    $py = "python"
    & $py "C:\giwanos\scripts\velos_client_write.py" $Room $Body $User
}
Set-Alias svm Send-VelosMessage

