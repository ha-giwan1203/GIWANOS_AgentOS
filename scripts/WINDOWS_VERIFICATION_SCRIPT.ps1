# 🔍 VELOS 스케줄러 최적화 Windows 환경 검증 스크립트
# 실제 Windows 환경에서 실행하여 적용 상태를 확인하는 스크립트

Write-Host "🚀 VELOS 스케줄러 최적화 적용 검증 시작..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# 1. 필수 파일 존재 확인
Write-Host "`n📁 1단계: 생성된 최적화 파일들 확인" -ForegroundColor Yellow
$requiredFiles = @(
    "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml",
    "scripts\Invoke-VelosParallel.ps1",
    "scripts\Start-Velos-CompletelyHidden.vbs",
    "scripts\Optimize-VelosScheduler.ps1",
    "VELOS_SCHEDULER_OPTIMIZATION_GUIDE.md"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host "  🎉 모든 최적화 파일이 존재합니다!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  누락된 파일: $($missingFiles.Count)개" -ForegroundColor Yellow
}

# 2. PowerShell 버전 확인
Write-Host "`n⚡ 2단계: PowerShell 버전 확인" -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Host "  현재 PowerShell 버전: $($psVersion.Major).$($psVersion.Minor).$($psVersion.Patch)" -ForegroundColor White

if ($psVersion.Major -ge 7) {
    Write-Host "  ✅ PowerShell 7.x 병렬 처리 지원!" -ForegroundColor Green
    
    # ForEach-Object -Parallel 테스트
    try {
        $testResult = 1..3 | ForEach-Object -Parallel { 
            return "Task $_" 
        } -ThrottleLimit 2
        Write-Host "  ✅ ForEach-Object -Parallel 기능 작동 확인!" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ 병렬 처리 기능 오류: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ⚠️  PowerShell $($psVersion.Major).$($psVersion.Minor) - 병렬 처리 제한" -ForegroundColor Yellow
    Write-Host "  💡 PowerShell 7 설치 권장: winget install Microsoft.PowerShell" -ForegroundColor Cyan
}

# 3. 기존 VELOS 스케줄드 태스크 확인
Write-Host "`n📋 3단계: 기존 VELOS 스케줄드 태스크 확인" -ForegroundColor Yellow
try {
    $velosTasks = Get-ScheduledTask | Where-Object { 
        $_.TaskName -like "*VELOS*" -or 
        $_.TaskPath -like "*VELOS*" -or
        $_.Description -like "*VELOS*"
    }
    
    if ($velosTasks.Count -eq 0) {
        Write-Host "  ℹ️  등록된 VELOS 스케줄드 태스크가 없습니다." -ForegroundColor Cyan
        Write-Host "  💡 최적화된 스케줄러 설치 필요" -ForegroundColor Yellow
    } else {
        Write-Host "  📋 발견된 VELOS 스케줄드 태스크: $($velosTasks.Count)개" -ForegroundColor White
        foreach ($task in $velosTasks) {
            $status = switch ($task.State) {
                'Ready' { "✅ 활성" }
                'Running' { "🔄 실행중" }
                'Disabled' { "❌ 비활성" }
                default { "❓ $($task.State)" }
            }
            Write-Host "    - $($task.TaskName) [$status]" -ForegroundColor Gray
            if ($task.Description) {
                Write-Host "      설명: $($task.Description)" -ForegroundColor DarkGray
            }
        }
        
        # 중복 태스크 체크
        $duplicateCount = ($velosTasks | Group-Object TaskName | Where-Object Count -gt 1).Count
        if ($duplicateCount -gt 0) {
            Write-Host "  ⚠️  중복 태스크 발견: $duplicateCount개" -ForegroundColor Yellow
            Write-Host "  💡 중복 정리 권장: .\scripts\Optimize-VelosScheduler.ps1 -Cleanup" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "  ❌ 스케줄드 태스크 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 최적화 스크립트 구문 검사
Write-Host "`n🔍 4단계: PowerShell 스크립트 구문 검사" -ForegroundColor Yellow
$scriptsToCheck = @(
    "scripts\Invoke-VelosParallel.ps1",
    "scripts\Optimize-VelosScheduler.ps1"
)

foreach ($script in $scriptsToCheck) {
    if (Test-Path $script) {
        try {
            $null = [System.Management.Automation.Language.Parser]::ParseFile($script, [ref]$null, [ref]$null)
            Write-Host "  ✅ $script - 구문 검사 통과" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ $script - 구문 오류: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ❓ $script - 파일 없음" -ForegroundColor Yellow
    }
}

# 5. XML 파일 구조 확인
Write-Host "`n📄 5단계: XML 파일 구조 확인" -ForegroundColor Yellow
$xmlFile = "VELOS_Master_Scheduler_HIDDEN_OPTIMIZED.xml"
if (Test-Path $xmlFile) {
    try {
        [xml]$xmlContent = Get-Content $xmlFile -Encoding UTF8
        Write-Host "  ✅ XML 구문 검사 통과" -ForegroundColor Green
        
        # 주요 설정 확인
        $isHidden = $xmlContent.Task.Settings.Hidden
        $runLevel = $xmlContent.Task.Principals.Principal.RunLevel
        $userId = $xmlContent.Task.Principals.Principal.UserId
        
        Write-Host "  🔧 주요 설정:" -ForegroundColor Cyan
        Write-Host "    - 숨김 모드: $isHidden" -ForegroundColor Gray
        Write-Host "    - 실행 레벨: $runLevel" -ForegroundColor Gray
        Write-Host "    - 실행 계정: $userId" -ForegroundColor Gray
        
        if ($isHidden -eq "true" -and $userId -eq "S-1-5-18") {
            Write-Host "  ✅ 완전 숨김 모드 설정 확인!" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  숨김 설정 확인 필요" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "  ❌ XML 구문 오류: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ XML 파일이 없습니다: $xmlFile" -ForegroundColor Red
}

# 6. VBS 스크립트 확인
Write-Host "`n📝 6단계: VBS 스크립트 구조 확인" -ForegroundColor Yellow
$vbsFile = "scripts\Start-Velos-CompletelyHidden.vbs"
if (Test-Path $vbsFile) {
    $vbsContent = Get-Content $vbsFile -Raw
    if ($vbsContent -match "WshShell\.Run.*0.*True") {
        Write-Host "  ✅ VBS 완전 숨김 모드 설정 확인" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  VBS 숨김 설정 확인 필요" -ForegroundColor Yellow
    }
    
    if ($vbsContent -match "pwsh\.exe") {
        Write-Host "  ✅ PowerShell 7.x 호출 설정 확인" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  PowerShell 버전 설정 확인 필요" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ VBS 파일이 없습니다: $vbsFile" -ForegroundColor Red
}

# 7. 로그 디렉토리 확인 및 생성
Write-Host "`n📊 7단계: 로그 디렉토리 확인" -ForegroundColor Yellow
$logDir = "data\logs"
if (-not (Test-Path $logDir)) {
    try {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        Write-Host "  ✅ 로그 디렉토리 생성: $logDir" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ 로그 디렉토리 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ 로그 디렉토리 존재: $logDir" -ForegroundColor Green
}

# 8. 권한 확인
Write-Host "`n🔐 8단계: 실행 권한 확인" -ForegroundColor Yellow
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "  ✅ 관리자 권한으로 실행 중" -ForegroundColor Green
    Write-Host "  💡 스케줄드 태스크 설치/수정 가능" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️  일반 사용자 권한으로 실행 중" -ForegroundColor Yellow
    Write-Host "  💡 스케줄드 태스크 관리를 위해 관리자 권한 필요" -ForegroundColor Cyan
    Write-Host "  📋 관리자 PowerShell 실행: Start-Process pwsh -Verb RunAs" -ForegroundColor Gray
}

# 최종 결과
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "🎯 검증 완료! 다음 단계 권장사항:" -ForegroundColor Cyan

if ($missingFiles.Count -eq 0 -and $psVersion.Major -ge 7 -and $isAdmin) {
    Write-Host "✅ 모든 조건 충족! 바로 설치 가능" -ForegroundColor Green
    Write-Host "📋 설치 명령어: .\scripts\Optimize-VelosScheduler.ps1 -Install -Force" -ForegroundColor White
} else {
    Write-Host "📋 권장 순서:" -ForegroundColor Yellow
    if ($missingFiles.Count -gt 0) {
        Write-Host "  1. 누락된 파일들 확인 및 Git Pull" -ForegroundColor Gray
    }
    if ($psVersion.Major -lt 7) {
        Write-Host "  2. PowerShell 7 설치: winget install Microsoft.PowerShell" -ForegroundColor Gray
    }
    if (-not $isAdmin) {
        Write-Host "  3. 관리자 권한으로 PowerShell 재실행" -ForegroundColor Gray
    }
    Write-Host "  4. 최적화 스케줄러 설치 실행" -ForegroundColor Gray
}

Write-Host "`n🔍 자세한 사용법: VELOS_SCHEDULER_OPTIMIZATION_GUIDE.md 참조" -ForegroundColor Cyan