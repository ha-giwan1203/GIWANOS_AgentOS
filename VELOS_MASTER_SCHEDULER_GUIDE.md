# VELOS 마스터 스케줄러 사용법 가이드

## 개요

VELOS 마스터 스케줄러는 Windows Task Scheduler와 연동하여 VELOS 시스템의 모든 작업을 자동으로 관리하는 중앙 집중식 스케줄링 시스템입니다.

## 주요 특징

- **단일 진입점**: Windows Task Scheduler는 5분마다 `run_giwanos_master_loop.py`만 실행
- **내부 디스패처**: 모든 잡(Daily/Weekly/Hourly)은 내부 디스패처가 판단하여 실행
- **VELOS 운영 철학 준수**: 파일명 고정, 자가 검증, 안전한 경로 관리
- **견고한 로깅**: 모든 실행 결과를 `data/logs/jobs.log`에 기록

## 파일 구조

```
C:\giwanos\
├── scripts\
│   ├── run_giwanos_master_loop.py          # 메인 스케줄러 (Windows Task Scheduler에서 실행)
│   ├── run_velos_master_scheduler.ps1      # PowerShell 래퍼 스크립트
│   ├── create_velos_master_scheduler_task.ps1  # Windows Task Scheduler 등록
│   └── test_velos_scheduler.ps1            # 테스트 스크립트
├── data\
│   ├── jobs.json                           # 잡 정의 파일
│   ├── job_state.json                      # 마지막 실행 시각 기록
│   └── logs\
│       └── jobs.log                        # 실행 로그
└── velos_master_scheduler.py               # 대안 스케줄러 (VELOS 모듈 통합)
```

## 기본 사용법

### 1. 잡 목록 조회

```powershell
python scripts\run_giwanos_master_loop.py --list
```

### 2. 특정 잡 강제 실행

```powershell
python scripts\run_giwanos_master_loop.py --force HealthCheck
```

### 3. 테스트용 시간 주입

```powershell
python scripts\run_giwanos_master_loop.py --now 2025-08-17T09:05
```

### 4. PowerShell 래퍼 사용

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\run_velos_master_scheduler.ps1 -DryRun -Verbose
```

## Windows Task Scheduler 등록

### 관리자 권한으로 실행

```powershell
# 관리자 PowerShell에서 실행
pwsh -ExecutionPolicy Bypass -File scripts\create_velos_master_scheduler_task.ps1
```

### 등록 확인

```powershell
# 태스크 목록 확인
schtasks /query /tn "VELOS Master Scheduler"

# 태스크 수동 실행
schtasks /run /tn "VELOS Master Scheduler"
```

### 태스크 제거

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\create_velos_master_scheduler_task.ps1 -Remove
```

## 테스트 및 검증

### 종합 테스트

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\test_velos_scheduler.ps1 -TestType all
```

### 개별 테스트

```powershell
# 기본 기능 테스트
pwsh -ExecutionPolicy Bypass -File scripts\test_velos_scheduler.ps1 -TestType basic

# 드라이런 테스트
pwsh -ExecutionPolicy Bypass -File scripts\test_velos_scheduler.ps1 -TestType dry-run

# 강제 실행 테스트
pwsh -ExecutionPolicy Bypass -File scripts\test_velos_scheduler.ps1 -TestType force
```

## 잡 설정 관리

### 기본 잡 설정

```json
[
  {
    "name": "DailyReport",
    "interval": "daily",
    "time": "09:05"
  },
  {
    "name": "WeeklyAudit", 
    "interval": "weekly",
    "day": "monday",
    "time": "09:30"
  },
  {
    "name": "HealthCheck",
    "interval": "hourly",
    "minute": 0
  }
]
```

### 잡 추가/수정

`data/jobs.json` 파일을 직접 편집하여 잡을 추가하거나 수정할 수 있습니다.

#### 지원하는 주기

- **daily**: 매일 지정된 시간에 실행
- **weekly**: 매주 지정된 요일과 시간에 실행
- **hourly**: 매시간 지정된 분에 실행

#### 잡 실행기 매핑

현재 등록된 잡과 실행 스크립트:

| 잡 이름 | 스크립트 | 설명 |
|---------|----------|------|
| DailyReport | `generate_velos_report_ko.py` | 일일 VELOS 보고서 생성 |
| WeeklyAudit | `check_velos_stats.py` | 주간 시스템 통계 확인 |
| HealthCheck | `check_velos_stats.py` | 시스템 상태 점검 |

## 로그 확인

### 실행 로그

```powershell
# 실시간 로그 확인
Get-Content C:\giwanos\data\logs\jobs.log -Wait

# 최근 로그 확인
Get-Content C:\giwanos\data\logs\jobs.log -Tail 20
```

### 테스트 로그

```powershell
# 테스트 로그 확인
Get-Content C:\giwanos\data\logs\scheduler_test.log -Tail 20
```

## 문제 해결

### 일반적인 문제

1. **Python 경로 문제**
   ```powershell
   # Python 경로 확인
   python --version
   ```

2. **VELOS_ROOT 환경변수**
   ```powershell
   # 환경변수 확인
   echo $env:VELOS_ROOT
   ```

3. **권한 문제**
   ```powershell
   # 관리자 권한으로 PowerShell 실행
   Start-Process powershell -Verb RunAs
   ```

### 로그 분석

실행 실패 시 `data/logs/jobs.log`를 확인하여 오류 원인을 파악할 수 있습니다.

## VELOS 운영 철학 준수

이 스케줄러는 VELOS 운영 철학을 완전히 준수합니다:

1. **파일명 고정**: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
2. **자가 검증 필수**: 수정/배포 전 자동·수동 테스트를 통과해야 함
3. **실행 결과 직접 테스트**: 코드 제공 시 실행 결과를 동봉/기록
4. **저장 경로 고정**: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
5. **실패 기록·회고**: 실패 로그를 남기고 후속 커밋/문서에 반영

## 개발자 정보

- **메인 스케줄러**: `scripts/run_giwanos_master_loop.py`
- **대안 스케줄러**: `velos_master_scheduler.py` (VELOS 모듈 통합 버전)
- **설정 파일**: `data/jobs.json`
- **상태 파일**: `data/job_state.json`
- **로그 파일**: `data/logs/jobs.log`

## 라이센스

VELOS 프로젝트의 일부로 제공됩니다.
