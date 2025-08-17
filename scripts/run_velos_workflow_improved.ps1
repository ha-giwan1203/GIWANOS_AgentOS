# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고, 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

# 개선된 VELOS 워크플로우 실행 스크립트
# 멈춤 원인 개선: 타임아웃, 에러 핸들링, 단계별 검증

param(
    [int]$TimeoutSeconds = 300,  # 5분 타임아웃
    [switch]$SkipTests = $false,
    [switch]$Verbose = $false
)

# 로깅 함수
function Write-VelosLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Level`: $Message"
}

# 안전한 명령 실행 함수
function Invoke-SafeCommand {
    param(
        [string]$Command,
        [string]$Description,
        [int]$Timeout = 60
    )

    Write-VelosLog "시작: $Description"

    try {
        $job = Start-Job -ScriptBlock {
            param($cmd)
            & python $cmd
        } -ArgumentList $Command

        if (Wait-Job $job -Timeout $Timeout) {
            $result = Receive-Job $job
            Remove-Job $job
            Write-VelosLog "완료: $Description"
            if ($Verbose) {
                $result | ForEach-Object { Write-Host "  $_" }
            }
            return $true
        } else {
            Stop-Job $job
            Remove-Job $job
            Write-VelosLog "타임아웃: $Description" "ERROR"
            return $false
        }
    } catch {
        Write-VelosLog "실패: $Description - $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# 메인 워크플로우
Write-VelosLog "VELOS 개선된 워크플로우 시작 (타임아웃: ${TimeoutSeconds}초)"

# 1. 환경 설정
Write-VelosLog "1단계: 환경 설정"
$envSetup = Invoke-SafeCommand -Command "scripts/setup_velos_env.ps1" -Description "환경 변수 설정" -Timeout 30

if (-not $envSetup) {
    Write-VelosLog "환경 설정 실패. 기본값으로 진행" "WARN"
}

# 2. 공통 유틸 검증
Write-VelosLog "2단계: 공통 유틸 검증"
$utilsTest = Invoke-SafeCommand -Command "modules/utils/velos_utils.py" -Description "공통 유틸 자가 검증" -Timeout 30

if (-not $utilsTest) {
    Write-VelosLog "공통 유틸 검증 실패. 계속 진행" "WARN"
}

# 3. DB 자동 복구
Write-VelosLog "3단계: DB 자동 복구"
$autoHeal = Invoke-SafeCommand -Command "scripts/auto_heal.py" -Description "DB 자동 복구" -Timeout 60

if (-not $autoHeal) {
    Write-VelosLog "DB 자동 복구 실패" "ERROR"
    exit 1
}

# 4. 호환성 뷰 적용
Write-VelosLog "4단계: 호환성 뷰 적용"
$applyViews = Invoke-SafeCommand -Command "scripts/apply_compat_views.py" -Description "호환성 뷰 적용" -Timeout 30

if (-not $applyViews) {
    Write-VelosLog "호환성 뷰 적용 실패" "ERROR"
    exit 1
}

# 5. 호환성 뷰 검증
Write-VelosLog "5단계: 호환성 뷰 검증"
$checkViews = Invoke-SafeCommand -Command "scripts/check_compat_views.py" -Description "호환성 뷰 검증" -Timeout 30

if (-not $checkViews) {
    Write-VelosLog "호환성 뷰 검증 실패" "ERROR"
    exit 1
}

# 6. 테스트 실행 (옵션)
if (-not $SkipTests) {
    Write-VelosLog "6단계: 테스트 실행"

    # 기본 FTS 테스트
    $basicTest = Invoke-SafeCommand -Command "scripts/test_fts.py" -Description "기본 FTS 테스트" -Timeout 60

    if (-not $basicTest) {
        Write-VelosLog "기본 FTS 테스트 실패" "WARN"
    }

    # 종합 테스트 (선택적)
    $comprehensiveTest = Invoke-SafeCommand -Command "scripts/test_fts_comprehensive.py" -Description "종합 FTS 테스트" -Timeout 120

    if (-not $comprehensiveTest) {
        Write-VelosLog "종합 FTS 테스트 실패" "WARN"
    }

    # 캐시 무효화 테스트
    $cacheTest = Invoke-SafeCommand -Command "scripts/test_cache_invalidation.py" -Description "캐시 무효화 테스트" -Timeout 60

    if (-not $cacheTest) {
        Write-VelosLog "캐시 무효화 테스트 실패" "WARN"
    }
}

# 7. 최종 통계 확인
Write-VelosLog "7단계: 최종 통계 확인"
$finalStats = Invoke-SafeCommand -Command "scripts/check_velos_stats.py" -Description "최종 통계 확인" -Timeout 30

if (-not $finalStats) {
    Write-VelosLog "최종 통계 확인 실패" "WARN"
}

# 8. 워크플로우 완료
Write-VelosLog "VELOS 워크플로우 완료"
Write-VelosLog "다음 명령으로 개별 테스트 가능:"
Write-VelosLog "  python scripts/test_fts.py"
Write-VelosLog "  python scripts/check_velos_stats.py"
Write-VelosLog "  python modules/utils/velos_utils.py"
