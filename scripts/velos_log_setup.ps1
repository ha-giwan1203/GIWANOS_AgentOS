# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

# VELOS 로그 디렉토리 설정 스크립트
# VELOS 로그 디렉토리를 확인하고 필요시 생성합니다.

param(
    [string]$LogDir = "C:\giwanos\data\logs",

    [switch]$Verbose = $false,

    [switch]$CreateSubDirs = $false,

    [switch]$SetPermissions = $false
)

# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# VSCode 렌더링 이슈 줄이기
$PSStyle.OutputRendering = "PlainText"

function Set-VelosLogDirectory {
    param(
        [string]$LogDir = "C:\giwanos\data\logs",
        [switch]$Verbose = $false,
        [switch]$CreateSubDirs = $false,
        [switch]$SetPermissions = $false
    )

    Write-Host "=== VELOS 로그 디렉토리 설정 ==="
    Write-Host "로그 디렉토리: $LogDir"

    try {
        # 로그 디렉토리 확인 및 생성
        if (!(Test-Path $LogDir)) {
            Write-Host "[CREATE] 로그 디렉토리 생성 중..."
            New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

            if (Test-Path $LogDir) {
                Write-Host "[SUCCESS] 로그 디렉토리 생성 완료: $LogDir"
            } else {
                throw "로그 디렉토리 생성 실패"
            }
        } else {
            Write-Host "[EXISTS] 로그 디렉토리가 이미 존재합니다: $LogDir"
        }

        # 하위 디렉토리 생성 (요청 시)
        if ($CreateSubDirs) {
            Write-Host "[SUBDIRS] 하위 디렉토리 생성 중..."

            $subDirs = @(
                "application",
                "error",
                "access",
                "performance",
                "security",
                "backup",
                "archive"
            )

            foreach ($subDir in $subDirs) {
                $fullSubDirPath = Join-Path $LogDir $subDir
                if (!(Test-Path $fullSubDirPath)) {
                    New-Item -ItemType Directory -Path $fullSubDirPath -Force | Out-Null
                    Write-Host "  [CREATE] $subDir 디렉토리 생성됨"
                } else {
                    Write-Host "  [EXISTS] $subDir 디렉토리 이미 존재"
                }
            }
        }

        # 권한 설정 (요청 시)
        if ($SetPermissions) {
            Write-Host "[PERMISSIONS] 로그 디렉토리 권한 설정 중..."
            try {
                $acl = Get-Acl $LogDir
                $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Users", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
                $acl.SetAccessRule($accessRule)
                Set-Acl $LogDir $acl
                Write-Host "[SUCCESS] 로그 디렉토리 권한 설정 완료"
            } catch {
                Write-Host "[WARN] 권한 설정 실패 (관리자 권한 필요): $_"
            }
        }

        # 디렉토리 정보 표시
        if ($Verbose) {
            Write-Host "`n=== 로그 디렉토리 정보 ==="
            $logDirInfo = Get-Item $LogDir
            Write-Host "경로: $($logDirInfo.FullName)"
            Write-Host "생성일: $($logDirInfo.CreationTime)"
            Write-Host "수정일: $($logDirInfo.LastWriteTime)"
            Write-Host "속성: $($logDirInfo.Attributes)"

            # 하위 항목 수 확인
            $subItems = Get-ChildItem $LogDir -Force | Measure-Object
            Write-Host "하위 항목 수: $($subItems.Count)"

            if ($subItems.Count -gt 0) {
                Write-Host "`n--- 하위 항목 목록 ---"
                Get-ChildItem $LogDir -Force | ForEach-Object {
                    $type = if ($_.PSIsContainer) { "DIR" } else { "FILE" }
                    Write-Host "  [$type] $($_.Name)"
                }
            }
        }

        # 환경 변수 설정
        $env:VELOS_LOG_DIR = $LogDir
        Write-Host "[ENV] VELOS_LOG_DIR 환경 변수 설정: $LogDir"

        return $true

    } catch {
        Write-Host "[ERROR] 로그 디렉토리 설정 실패: $_"
        return $false
    }
}

function Test-VelosLogDirectory {
    param(
        [string]$LogDir = "C:\giwanos\data\logs"
    )

    Write-Host "=== VELOS 로그 디렉토리 테스트 ==="

    $testResults = @{
        "디렉토리 존재" = $false
        "쓰기 권한" = $false
        "읽기 권한" = $false
        "테스트 파일 생성" = $false
    }

    try {
        # 디렉토리 존재 확인
        if (Test-Path $LogDir) {
            $testResults["디렉토리 존재"] = $true
            Write-Host "✓ 디렉토리 존재 확인"

            # 쓰기 권한 테스트
            $testFile = Join-Path $LogDir "test_write_$(Get-Date -Format 'yyyyMMdd_HHmmss').tmp"
            try {
                "VELOS 로그 디렉토리 테스트" | Out-File -FilePath $testFile -Encoding UTF8
                $testResults["쓰기 권한"] = $true
                Write-Host "✓ 쓰기 권한 확인"

                # 읽기 권한 테스트
                $content = Get-Content $testFile -Raw
                if ($content) {
                    $testResults["읽기 권한"] = $true
                    Write-Host "✓ 읽기 권한 확인"
                }

                # 테스트 파일 삭제
                Remove-Item $testFile -Force
                $testResults["테스트 파일 생성"] = $true
                Write-Host "✓ 테스트 파일 생성/삭제 확인"

            } catch {
                Write-Host "✗ 쓰기/읽기 권한 테스트 실패: $_"
            }
        } else {
            Write-Host "✗ 디렉토리가 존재하지 않습니다"
        }

    } catch {
        Write-Host "[ERROR] 로그 디렉토리 테스트 실패: $_"
    }

    # 결과 요약
    Write-Host "`n=== 테스트 결과 요약 ==="
    foreach ($test in $testResults.GetEnumerator()) {
        $status = if ($test.Value) { "✓" } else { "✗" }
        Write-Host "$status $($test.Key): $($test.Value)"
    }

    return $testResults
}

# 메인 실행
$success = Set-VelosLogDirectory -LogDir $LogDir -Verbose:$Verbose -CreateSubDirs:$CreateSubDirs -SetPermissions:$SetPermissions

if ($success) {
    Write-Host "`n[SUCCESS] VELOS 로그 디렉토리 설정 완료"

    # 테스트 실행
    Test-VelosLogDirectory -LogDir $LogDir
} else {
    Write-Host "`n[FAILED] VELOS 로그 디렉토리 설정 실패"
}

Write-Host "`n=== VELOS 로그 디렉토리 설정 완료 ==="
