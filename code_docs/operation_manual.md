
# GIWANOS AgentOS 상세 운영 매뉴얼

## 1. 시스템 실행 방법

### 자동 실행
PowerShell을 열고 아래 명령을 실행하여 시스템을 자동 실행합니다.
```powershell
cd C:/giwanos
python giwanos_agent/controller.py auto
```

### 수동 계획 실행
아래 명령을 실행하여 작업 계획을 확인합니다.
```powershell
cd C:/giwanos
python giwanos_agent/controller.py plan
```

## 2. 주요 폴더 구조
```
C:/giwanos
├── advanced_modules (RAG 관련 모듈)
├── giwanos_agent (중앙 관리 에이전트)
├── notion_integration (Notion 연동)
├── system (GitHub 연동 및 자동화)
├── interface (Streamlit 대시보드)
├── reports (PDF 생성 및 이메일 발송)
├── scheduling (자동화 스케줄링)
├── security (보안 및 민감정보 관리)
├── vector_cache (벡터 DB 관리)
├── logs (로그 데이터 저장)
└── docs (운영 매뉴얼 및 문서화)
```

## 3. 문제 발생 시 대응 방법

- PowerShell 실행 오류 시:
```powershell
Remove-Module PSReadLine
Import-Module PSReadLine
```

- Python 실행 오류 시:
  1. Python 설치 확인 및 재설치
  2. 환경 변수(PATH) 설정 확인

## 4. 유지보수

- 주기적 백업: 매주 로그 데이터 백업 권장
- 주기적 시스템 점검: 월 1회 시스템 전체 통합 테스트 진행

## 5. 비상 연락망

시스템 문제 발생 시 즉시 관리자에게 보고하여 문제를 빠르게 해결합니다.
