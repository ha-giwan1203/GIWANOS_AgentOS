# scripts/auto_dispatch.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 VELOS 자동 디스패치 시작" -ForegroundColor Green
Write-Host "=" * 40

# 환경변수 로딩
$envFile = "C:\giwanos\configs\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "✅ 환경변수 로드 완료" -ForegroundColor Green
} else {
    Write-Host "⚠️  환경변수 파일을 찾을 수 없습니다: $envFile" -ForegroundColor Yellow
}

# 최신 파일 찾기
$autoDir = "C:\giwanos\data\reports\auto"
$latestPdf = Get-ChildItem -Path $autoDir -Filter "velos_auto_report_*_ko.pdf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestMd = Get-ChildItem -Path $autoDir -Filter "velos_auto_report_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $latestPdf) {
    Write-Host "❌ PDF 파일을 찾을 수 없습니다" -ForegroundColor Red
    exit 1
}

Write-Host "📄 최신 파일:" -ForegroundColor Cyan
Write-Host "   PDF: $($latestPdf.Name)" -ForegroundColor White
if ($latestMd) {
    Write-Host "   MD:  $($latestMd.Name)" -ForegroundColor White
} else {
    Write-Host "   MD:  없음" -ForegroundColor Yellow
}

# 자동 디스패치 실행
Write-Host "`n📤 자동 디스패치 실행 중..." -ForegroundColor Cyan

try {
    # Python 스크립트 실행
    $pythonArgs = @(
        "-c",
        @"
import sys
sys.path.append(r'C:\giwanos\scripts')
from dispatch_report import dispatch_report
from pathlib import Path

try:
    auto_dir = Path(r'C:\giwanos\data\reports\auto')
    latest_pdf = max(auto_dir.glob('velos_auto_report_*_ko.pdf'))
    latest_md = max(auto_dir.glob('velos_auto_report_*.md'), default=None)

    results = dispatch_report(latest_pdf, latest_md, title='VELOS 한국어 종합 보고서')

    # 결과 분석
    success_count = sum(1 for v in results.values() if isinstance(v, dict) and v.get('ok'))
    total_count = len([k for k in results.keys() if k in ['slack', 'notion', 'email', 'push']])

    print(f'✅ 디스패치 완료: {success_count}/{total_count} 채널 성공')

    # 실패한 채널 출력
    for channel, result in results.items():
        if isinstance(result, dict) and not result.get('ok'):
            print(f'   ⚠️  {channel}: {result.get(\"detail\", \"unknown error\")}')

    exit(0 if success_count > 0 else 1)

except Exception as e:
    print(f'❌ 디스패치 실패: {e}')
    exit(1)
"@
    )

    & python @pythonArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 자동 디스패치 성공!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n❌ 자동 디스패치 실패" -ForegroundColor Red
        exit 1
    }

} catch {
    Write-Host "`n❌ 자동 디스패치 오류: $_" -ForegroundColor Red
    exit 1
}
