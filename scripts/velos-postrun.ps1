# VELOS Postrun Script
# VELOS 마스터 루프 실행 후 자동 실행되는 후처리 스크립트

param(
    [switch]$Verbose,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# VELOS 루트 경로 설정
$VELOS_ROOT = "C:\giwanos"
Set-Location $VELOS_ROOT

# 로그 함수
function Write-VelosLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

try {
    Write-VelosLog "VELOS Postrun 스크립트 시작" "INFO"
    
    # 1. 최신 보고서 확인
    $latestReport = Get-ChildItem "$VELOS_ROOT\data\reports\auto\velos_auto_report_*.md" | 
                   Sort-Object LastWriteTime -Descending | 
                   Select-Object -First 1
    
    if ($latestReport) {
        Write-VelosLog "최신 보고서 발견: $($latestReport.Name)" "INFO"
        
        # 2. 메모리 동기화
        Write-VelosLog "메모리 동기화 시작" "INFO"
        python -c "
import sys
sys.path.append('.')
from modules.core.memory_adapter import create_memory_adapter
adapter = create_memory_adapter()
json_processed = adapter.flush_jsonl_to_json()
db_processed = adapter.flush_jsonl_to_db()
print(f'JSON 동기화: {json_processed}개, DB 동기화: {db_processed}개')
"
        
        # 3. 시스템 상태 확인
        Write-VelosLog "시스템 상태 확인" "INFO"
        python scripts\velos_cursor_interface.py --status
        
        # 4. Git 자동 커밋 (변경사항이 있는 경우)
        Write-VelosLog "Git 상태 확인" "INFO"
        $gitStatus = git status --porcelain
        if ($gitStatus) {
            Write-VelosLog "변경사항 발견, 자동 커밋 실행" "INFO"
            git add .
            git commit -m "VELOS Auto Update - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            
            # 원격 저장소가 설정된 경우 푸시
            $remoteUrl = git config --get remote.origin.url
            if ($remoteUrl) {
                Write-VelosLog "원격 저장소에 푸시" "INFO"
                git push
            }
        } else {
            Write-VelosLog "변경사항 없음" "INFO"
        }
        
        # 5. 시스템 정리
        Write-VelosLog "시스템 정리 시작" "INFO"
        
        # 오래된 로그 파일 정리 (30일 이상)
        $logFiles = Get-ChildItem "$VELOS_ROOT\logs\*.log" -ErrorAction SilentlyContinue
        $oldLogs = $logFiles | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
        if ($oldLogs) {
            Write-VelosLog "오래된 로그 파일 정리: $($oldLogs.Count)개" "INFO"
            $oldLogs | Remove-Item -Force
        }
        
        # 임시 파일 정리
        $tempFiles = Get-ChildItem "$VELOS_ROOT\*.tmp" -ErrorAction SilentlyContinue
        if ($tempFiles) {
            Write-VelosLog "임시 파일 정리: $($tempFiles.Count)개" "INFO"
            $tempFiles | Remove-Item -Force
        }
        
        # 6. 성능 통계 수집
        Write-VelosLog "성능 통계 수집" "INFO"
        $memoryStats = python -c "
import sys
sys.path.append('.')
from modules.core.memory_adapter import create_memory_adapter
adapter = create_memory_adapter()
stats = adapter.get_stats()
print('버퍼: ' + str(stats['buffer_size']) + ', DB: ' + str(stats['db_records']) + ', JSON: ' + str(stats['json_records']))
"
        
        # 7. 완료 보고서 생성
        $postrunReport = @"
# VELOS Postrun Report
생성 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 실행 결과
- 최신 보고서: $($latestReport.Name)
- 메모리 통계: $memoryStats
- Git 커밋: $(if ($gitStatus) { '실행됨' } else { '변경사항 없음' })
- 정리된 파일: $($oldLogs.Count + $tempFiles.Count)개

## 시스템 상태
- VELOS 루트: $VELOS_ROOT
- 작업 디렉토리: $(Get-Location)
- 실행 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---
*이 보고서는 velos-postrun.ps1에 의해 자동 생성되었습니다.*
"@
        
        $postrunReportPath = "$VELOS_ROOT\data\reports\auto\velos_postrun_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
        $postrunReport | Out-File -FilePath $postrunReportPath -Encoding UTF8
        
        Write-VelosLog "Postrun 보고서 생성: $postrunReportPath" "INFO"
        
    } else {
        Write-VelosLog "최신 보고서를 찾을 수 없습니다" "WARN"
    }
    
    Write-VelosLog "VELOS Postrun 스크립트 완료" "INFO"
    
} catch {
    Write-VelosLog "오류 발생: $($_.Exception.Message)" "ERROR"
    Write-VelosLog "스택 트레이스: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

# 성공적으로 완료
Write-VelosLog "VELOS Postrun 스크립트가 성공적으로 완료되었습니다" "SUCCESS"
exit 0
