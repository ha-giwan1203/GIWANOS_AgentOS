
# VELOS 스케줄러 진단 스크립트
Write-Host "=== VELOS 스케줄러 진단 시작 ===" -ForegroundColor Green

# 1. VELOS 관련 활성 작업 조회
Write-Host "`n1. VELOS 관련 스케줄러 작업:" -ForegroundColor Yellow
$velosTasks = Get-ScheduledTask | Where-Object {$_.TaskName -like "*VELOS*"}
$velosTasks | Select-Object TaskName, State, TaskPath | Format-Table -AutoSize

# 2. 현재 실행 중인 VELOS 작업
Write-Host "`n2. 현재 실행 중인 VELOS 작업:" -ForegroundColor Yellow
$runningTasks = Get-ScheduledTask | Where-Object {$_.State -eq "Running" -and $_.TaskName -like "*VELOS*"}
if ($runningTasks.Count -gt 0) {
    $runningTasks | Select-Object TaskName, State | Format-Table -AutoSize
} else {
    Write-Host "현재 실행 중인 VELOS 작업 없음" -ForegroundColor Gray
}

# 3. 최근 실행 이력 (창이 나타난 시점 추적)
Write-Host "`n3. 최근 VELOS 작업 실행 이력:" -ForegroundColor Yellow
foreach ($task in $velosTasks) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName $task.TaskName -ErrorAction SilentlyContinue
    if ($taskInfo) {
        Write-Host "작업: $($task.TaskName)" -ForegroundColor Cyan
        Write-Host "  마지막 실행: $($taskInfo.LastRunTime)"
        Write-Host "  다음 실행: $($taskInfo.NextRunTime)"
        Write-Host "  마지막 결과: $($taskInfo.LastTaskResult)"
    }
}

# 4. Hidden 설정 확인을 위한 XML 내용 검사
Write-Host "`n4. Hidden 설정 검사:" -ForegroundColor Yellow
$taskFolder = "C:\Windows\System32\Tasks"
Get-ChildItem -Path $taskFolder -Recurse -Filter "*VELOS*" -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    $isHidden = $content -match "<Hidden>true</Hidden>"
    $taskName = $_.Name
    if ($isHidden) {
        Write-Host "  ✅ $taskName - Hidden 설정됨" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $taskName - Hidden 설정 안됨 (창 노출 원인!)" -ForegroundColor Red
    }
}

Write-Host "`n=== 진단 완료 ===" -ForegroundColor Green
Write-Host "위 결과를 Claude AI에게 전달하여 정확한 수정 방안을 받으세요." -ForegroundColor Yellow
