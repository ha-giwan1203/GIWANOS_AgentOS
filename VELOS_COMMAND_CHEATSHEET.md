# VELOS 시스템 명령어 치트시트

## 🚀 빠른 시작 (가장 자주 사용)

### 시스템 상태 확인
```bash
# 30초 빠른 확인 (가장 중요!)
python scripts/py/velos_quick_status.py

# 2분 전체 테스트
python scripts/py/velos_pipeline_test.py

# 1분 상세 점검
python scripts/py/velos_system_integration_check.py
```

### 보고서 생성
```bash
# 자동 보고서 생성
python scripts/auto_generate_runner.py

# AI 인사이트 보고서
python scripts/velos_ai_insights_report.py
```

### 알림 테스트
```bash
# 전체 알림 전송
python scripts/dispatch_report.py

# Notion만 테스트
python scripts/py/velos_notion_enhanced_dispatch.py
```

---

## 🔧 시스템 관리

### 데이터베이스 관리
```bash
# 데이터베이스 백업
python scripts/backup_velos_db.py

# 데이터베이스 재생성
python scripts/py/recreate_velos_db.py

# FTS 상태 확인
python scripts/py/fts_healthcheck.py
```

### 환경변수 관리
```bash
# 환경변수 진단
python scripts/py/velos_env_check.py

# 알림 시스템 진단
python scripts/py/velos_notification_check.py

# Notion 토큰 진단
python scripts/py/velos_notion_token_refresh.py
```

---

## 🔍 문제 진단

### 단계별 진단
```bash
# 1단계: 기본 상태 확인
python scripts/py/velos_quick_status.py

# 2단계: 환경변수 확인
python scripts/py/velos_env_check.py

# 3단계: 알림 시스템 확인
python scripts/py/velos_notification_check.py

# 4단계: Notion 연결 확인
python scripts/py/velos_notion_token_refresh.py

# 5단계: 전체 시스템 확인
python scripts/py/velos_system_integration_check.py
```

### 특정 문제 진단
```bash
# dispatch_report.py 401 오류 진단
python scripts/py/velos_dispatch_debug.py

# Notion 필드 매핑 문제 진단
python scripts/py/velos_notion_field_fix.py

# 시스템 연동 문제 진단
python scripts/py/velos_system_integration_check.py
```

---

## 📊 모니터링 및 로그

### 로그 확인
```bash
# 전송 로그 확인
ls data/reports/_dispatch/

# 시스템 로그 확인
ls data/logs/

# 최신 보고서 확인
ls data/reports/auto/velos_auto_report_*_ko.pdf | tail -1
```

### 성능 모니터링
```bash
# 시스템 성능 점검
python scripts/py/velos_system_integration_check.py

# 파이프라인 성능 테스트
python scripts/py/velos_pipeline_test.py
```

---

## 🛠️ 고급 관리

### Notion 관리
```bash
# 필드 매핑 재생성
python scripts/py/velos_notion_field_discovery.py

# 필드 매핑 수정
python scripts/py/velos_notion_field_fix.py

# 향상된 전송 테스트
python scripts/py/velos_notion_enhanced_dispatch.py

# 통합 관리
python scripts/py/velos_notion_integration.py

# 고급 쿼리
python scripts/py/velos_notion_advanced_queries.py

# 워크플로우 자동화
python scripts/py/velos_notion_workflow_automation.py
```

### 코드 품질 관리
```bash
# 코드 품질 개선
python scripts/py/velos_code_quality.py

# 보안 점검
python scripts/py/velos_security_check.py

# 의존성 설치
pip install requests python-dotenv pushbullet.py
```

---

## 🔄 자동화 스크립트

### PowerShell 자동화
```powershell
# 전체 시스템 설정
powershell -ExecutionPolicy Bypass -File scripts/ps/velos_complete_setup.ps1

# 스케줄러 등록
powershell -ExecutionPolicy Bypass -File scripts/ps/register_velos_maintenance.ps1

# 로그 로테이션
powershell -ExecutionPolicy Bypass -File scripts/ps/rotate_logs.ps1

# 백업 정리
powershell -ExecutionPolicy Bypass -File scripts/ps/cleanup_backups.ps1
```

### Python 자동화
```bash
# 자동 보고서 생성 (백그라운드)
python scripts/auto_generate_runner.py &

# 자동 디스패치
python scripts/dispatch_report.py

# 자동 시스템 점검
python scripts/py/velos_system_integration_check.py
```

---

## 🚨 긴급 상황 대응

### 시스템 복구
```bash
# 1. 환경변수 복구
python scripts/py/velos_env_check.py

# 2. 데이터베이스 복구
python scripts/py/recreate_velos_db.py

# 3. 알림 시스템 복구
python scripts/py/velos_notification_fix.py

# 4. 전체 시스템 점검
python scripts/py/velos_system_integration_check.py
```

### 특정 오류 해결
```bash
# Notion 401 오류
python scripts/py/velos_notion_token_refresh.py

# 이메일 전송 실패
python scripts/py/velos_notification_fix.py

# 보고서 생성 실패
python scripts/auto_generate_runner.py
```

---

## 📋 일일 점검 체크리스트

### 매일 확인할 항목
```bash
# 1. 시스템 상태 확인 (30초)
python scripts/py/velos_quick_status.py

# 2. 최신 보고서 확인
ls data/reports/auto/velos_auto_report_*_ko.pdf | tail -1

# 3. 알림 전송 테스트
python scripts/dispatch_report.py

# 4. 로그 확인
ls data/reports/_dispatch/ | tail -5
```

### 주간 점검
```bash
# 1. 전체 시스템 점검
python scripts/py/velos_system_integration_check.py

# 2. 파이프라인 테스트
python scripts/py/velos_pipeline_test.py

# 3. 백업 확인
ls backup/ | tail -5

# 4. 성능 점검
python scripts/py/velos_code_quality.py
```

---

## 🎯 상황별 명령어

### 처음 사용할 때
```bash
# 1. 시스템 상태 확인
python scripts/py/velos_quick_status.py

# 2. 환경변수 설정 확인
python scripts/py/velos_env_check.py

# 3. 전체 테스트
python scripts/py/velos_pipeline_test.py
```

### 문제가 생겼을 때
```bash
# 1. 빠른 진단
python scripts/py/velos_quick_status.py

# 2. 상세 진단
python scripts/py/velos_system_integration_check.py

# 3. 특정 문제 진단 (오류 메시지에 따라)
python scripts/py/velos_notion_token_refresh.py  # Notion 문제
python scripts/py/velos_notification_check.py   # 알림 문제
```

### 새로운 기능 테스트할 때
```bash
# 1. 기존 상태 백업
python scripts/backup_velos_db.py

# 2. 기능 테스트
python scripts/py/새로운_기능_스크립트.py

# 3. 결과 확인
python scripts/py/velos_quick_status.py
```

---

## 💡 팁과 트릭

### 효율적인 사용법
- **가장 중요한 명령어**: `python scripts/py/velos_quick_status.py`
- **문제 진단 순서**: 빠른 확인 → 상세 진단 → 특정 진단
- **정기 점검**: 매일 빠른 확인, 주간 전체 점검

### 자주 하는 실수
- 환경변수 파일 위치: `configs/.env` (not `configs/security/env.local`)
- Notion 토큰 형식: `ntn_` 형식이 정상 (not `secret_`)
- 파일 경로: Windows에서는 `C:\giwanos` 사용

### 성능 최적화
- 빠른 확인은 30초, 전체 테스트는 2분 소요
- 백그라운드 실행으로 다른 작업과 병렬 처리
- 로그 파일 정기 정리로 디스크 공간 절약

---

**💡 핵심: `python scripts/py/velos_quick_status.py`가 가장 중요합니다!**

*마지막 업데이트: 2025-08-19 21:07*
