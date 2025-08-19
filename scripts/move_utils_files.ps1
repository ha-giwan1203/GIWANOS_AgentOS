# [ACTIVE] VELOS utils 파일 이동 시스템 - utils 파일 이동 및 의존성 수정 스크립트
# VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

Write-Host "=== VELOS utils 파일 이동 및 의존성 수정 ===" -ForegroundColor Yellow

# 1. modules/utils 폴더 생성
Write-Host "`n[1] modules/utils 폴더 생성..." -ForegroundColor Cyan
if (!(Test-Path "modules/utils")) {
    New-Item -ItemType Directory -Path "modules/utils" -Force
    Write-Host "✓ modules/utils 폴더 생성됨" -ForegroundColor Green
} else {
    Write-Host "✓ modules/utils 폴더 이미 존재" -ForegroundColor Green
}

# 2. 파일 이동
Write-Host "`n[2] utils 파일들을 modules/utils로 이동..." -ForegroundColor Cyan

$filesToMove = @(
    "utils/net.py",
    "utils/utf8_force.py", 
    "utils/memory_adapter.py"
)

foreach ($file in $filesToMove) {
    if (Test-Path $file) {
        $destPath = $file -replace "^utils/", "modules/utils/"
        Copy-Item $file $destPath -Force
        Write-Host "✓ $file → $destPath" -ForegroundColor Green
    } else {
        Write-Host "⚠ $file 파일이 없습니다" -ForegroundColor Yellow
    }
}

# 3. 의존성 수정할 파일들
Write-Host "`n[3] 의존성 수정할 파일들 확인..." -ForegroundColor Cyan

$filesToUpdate = @(
    "scripts/notion_memory_db.py",
    "scripts/dispatch_slack.py", 
    "scripts/dispatch_report.py",
    "scripts/dispatch_push.py",
    "scripts/dispatch_notion.py",
    "scripts/notion_memory_page.py",
    "dashboard/app.py",
    "scripts/check_env.py",
    "scripts/velos_dashboard.py",
    "modules/memory/router/velos_router_adapter.py",
    "modules/core/context_builder.py"
)

Write-Host "총 $($filesToUpdate.Count)개 파일의 import 경로를 수정해야 합니다." -ForegroundColor White

# 4. 각 파일의 import 문 수정
Write-Host "`n[4] import 경로 수정..." -ForegroundColor Cyan

foreach ($file in $filesToUpdate) {
    if (Test-Path $file) {
        Write-Host "수정 중: $file" -ForegroundColor White
        
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # utils.net → modules.utils.net
        $content = $content -replace "from utils\.net", "from modules.utils.net"
        $content = $content -replace "import utils\.net", "import modules.utils.net"
        
        # utils.utf8_force → modules.utils.utf8_force  
        $content = $content -replace "from utils\.utf8_force", "from modules.utils.utf8_force"
        $content = $content -replace "import utils\.utf8_force", "import modules.utils.utf8_force"
        
        # utils.memory_adapter → modules.utils.memory_adapter
        $content = $content -replace "from utils\.memory_adapter", "from modules.utils.memory_adapter"
        $content = $content -replace "import utils\.memory_adapter", "import modules.utils.memory_adapter"
        
        Set-Content $file $content -Encoding UTF8
        Write-Host "  ✓ $file 수정 완료" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $file 파일이 없습니다" -ForegroundColor Yellow
    }
}

# 5. 이동 완료 후 원본 파일 삭제
Write-Host "`n[5] 원본 utils 파일들 삭제..." -ForegroundColor Cyan

foreach ($file in $filesToMove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "✓ $file 삭제됨" -ForegroundColor Green
    }
}

# 6. 빈 utils 폴더 확인
Write-Host "`n[6] utils 폴더 상태 확인..." -ForegroundColor Cyan
$remainingFiles = Get-ChildItem "utils" -File | Where-Object { $_.Name -ne "__pycache__" }
if ($remainingFiles.Count -eq 0) {
    Write-Host "✓ utils 폴더가 비어있습니다" -ForegroundColor Green
} else {
    Write-Host "⚠ utils 폴더에 남은 파일들:" -ForegroundColor Yellow
    $remainingFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }
}

Write-Host "`n=== 작업 완료 ===" -ForegroundColor Yellow
Write-Host "다음 단계: Python 모듈 테스트 실행" -ForegroundColor Cyan

