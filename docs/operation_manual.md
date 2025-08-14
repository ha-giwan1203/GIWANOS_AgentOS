# VELOS 운영 매뉴얼

## 목차
1. [시스템 요구사항](#1-시스템-요구사항)
2. [설치 및 초기 설정](#2-설치-및-초기-설정)
3. [환경변수 설정](#3-환경변수-설정)
4. [실행 및 운영](#4-실행-및-운영)
5. [백업 및 복구](#5-백업-및-복구)
6. [모니터링 및 로그](#6-모니터링-및-로그)
7. [문제 해결](#7-문제-해결)
8. [유지보수](#8-유지보수)

---

## 1. 시스템 요구사항

### 1.1 하드웨어 요구사항
- **CPU**: Intel i5 이상 또는 AMD Ryzen 5 이상
- **메모리**: 최소 8GB RAM (권장 16GB)
- **저장공간**: 최소 10GB 여유 공간
- **네트워크**: 인터넷 연결 (외부 API 연동용)

### 1.2 소프트웨어 요구사항
- **운영체제**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 이상 (권장 3.11)
- **Git**: 버전 관리용

### 1.3 필수 Python 패키지
```bash
pip install -r configs/requirements.txt
```

---

## 2. 설치 및 초기 설정

### 2.1 프로젝트 다운로드
```bash
git clone <repository-url>
cd giwanos
```

### 2.2 가상환경 설정 (권장)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2.3 의존성 설치
```bash
pip install -r configs/requirements.txt
```

### 2.4 초기 디렉토리 생성
```bash
python -c "from modules.report_paths import ensure_dirs; ensure_dirs()"
```

---

## 3. 환경변수 설정

### 3.1 .env 파일 생성
`configs/.env` 파일을 생성하고 다음 내용을 입력:

```env
# VELOS 시스템 설정
VELOS_ROOT=C:\giwanos

# Slack 설정
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C0123456789
SLACK_APP_TOKEN=xapp-your-app-token

# Notion 설정
NOTION_TOKEN=secret-your-notion-token
NOTION_PARENT_PAGE_ID=your-page-id

# 이메일 설정 (선택사항)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# OpenAI 설정 (선택사항)
OPENAI_API_KEY=sk-your-openai-key
```

### 3.2 환경변수 검증
```bash
python -c "from modules.report_paths import env_presence; print(env_presence())"
```

---

## 4. 실행 및 운영

### 4.1 메인 루프 실행
```bash
python scripts/run_giwanos_master_loop.py
```

### 4.2 브릿지 시스템 실행
```bash
python scripts/velos_bridge.py
```

### 4.3 AI 인사이트 보고서 생성
```bash
python scripts/velos_ai_insights_report.py
```

### 4.4 자동화 스케줄링 (Windows)
```powershell
# 작업 스케줄러에 등록
schtasks /create /tn "VELOS_Master_Loop" /tr "python C:\giwanos\scripts\run_giwanos_master_loop.py" /sc daily /st 09:00
schtasks /create /tn "VELOS_Bridge" /tr "python C:\giwanos\scripts\velos_bridge.py" /sc minute /mo 5
```

### 4.5 자동화 스케줄링 (Linux/macOS)
```bash
# crontab 편집
crontab -e

# 다음 내용 추가
0 9 * * * cd /path/to/giwanos && python scripts/run_giwanos_master_loop.py
*/5 * * * * cd /path/to/giwanos && python scripts/velos_bridge.py
```

---

## 5. 백업 및 복구

### 5.1 수동 백업
```bash
# 전체 시스템 백업
python scripts/backup_velos_db.py

# 메모리 백업
cp data/memory/learning_memory.json data/backups/learning_memory_$(date +%Y%m%d_%H%M%S).json
```

### 5.2 자동 백업 설정
```bash
# Windows
schtasks /create /tn "VELOS_Backup" /tr "python C:\giwanos\scripts\backup_velos_db.py" /sc daily /st 01:00

# Linux/macOS
0 1 * * * cd /path/to/giwanos && python scripts/backup_velos_db.py
```

### 5.3 복구 절차
```bash
# 1. 시스템 중지
# 2. 백업 파일 복원
cp data/backups/velos_YYYYMMDD_HHMMSS.db data/velos.db
cp data/backups/learning_memory_YYYYMMDD_HHMMSS.json data/memory/learning_memory.json

# 3. 시스템 재시작
python scripts/run_giwanos_master_loop.py
```

---

## 6. 모니터링 및 로그

### 6.1 로그 파일 위치
- **시스템 로그**: `data/logs/velos_bridge.log`
- **자동화 로그**: `data/logs/autofix.log`
- **API 비용 로그**: `data/logs/api_cost_log.json`

### 6.2 시스템 상태 확인
```bash
# 시스템 헬스 확인
python -c "import json; print(json.dumps(json.load(open('data/logs/system_health.json')), indent=2))"

# 메모리 상태 확인
python -c "import json; data=json.load(open('data/memory/learning_memory.json')); print(f'메모리 항목 수: {len(data)}')"
```

### 6.3 실시간 모니터링
```bash
# 로그 실시간 확인
tail -f data/logs/velos_bridge.log

# 시스템 리소스 확인
python scripts/update_system_health.py
```

---

## 7. 문제 해결

### 7.1 일반적인 오류 및 해결방법

#### 7.1.1 Import 오류
**증상**: `ModuleNotFoundError: No module named 'modules'`
**해결방법**:
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# 또는
set PYTHONPATH=%PYTHONPATH%;%CD%
```

#### 7.1.2 Slack 전송 오류
**증상**: `Slack 실패: invalid_auth`
**해결방법**:
1. `SLACK_BOT_TOKEN` 확인
2. Bot 권한 확인 (chat:write, files:write)
3. 채널 ID 확인

#### 7.1.3 메모리 파일 오류
**증상**: `JSONDecodeError`
**해결방법**:
```bash
# 메모리 파일 백업 후 재생성
cp data/memory/learning_memory.json data/backups/
echo '{"meta":{"created_by":"recovery","version":1},"records":[]}' > data/memory/learning_memory.json
```

#### 7.1.4 권한 오류
**증상**: `PermissionError: [Errno 13] Permission denied`
**해결방법**:
```bash
# 폴더 권한 확인 및 수정
chmod -R 755 data/
chmod -R 755 logs/
```

### 7.2 성능 문제 해결

#### 7.2.1 메모리 사용량 높음
**해결방법**:
```bash
# 오래된 로그 정리
find data/logs/ -name "*.log" -mtime +30 -delete
find data/reports/auto/ -name "*.md" -mtime +7 -delete
```

#### 7.2.2 디스크 공간 부족
**해결방법**:
```bash
# 백업 파일 정리 (30일 이상)
find data/backups/ -name "*.db" -mtime +30 -delete
find data/backups/ -name "*.json" -mtime +30 -delete
```

### 7.3 네트워크 문제 해결

#### 7.3.1 API 연결 실패
**해결방법**:
1. 인터넷 연결 확인
2. 방화벽 설정 확인
3. 프록시 설정 확인

---

## 8. 유지보수

### 8.1 정기 점검 (주간)
- [ ] 시스템 로그 확인
- [ ] 백업 파일 정상성 확인
- [ ] 디스크 공간 확인
- [ ] API 토큰 유효성 확인

### 8.2 정기 점검 (월간)
- [ ] 시스템 성능 분석
- [ ] 메모리 사용량 분석
- [ ] 오류 패턴 분석
- [ ] 설정 파일 업데이트

### 8.3 업데이트 절차
```bash
# 1. 현재 상태 백업
python scripts/backup_velos_db.py

# 2. 코드 업데이트
git pull origin main

# 3. 의존성 업데이트
pip install -r configs/requirements.txt --upgrade

# 4. 시스템 재시작
python scripts/run_giwanos_master_loop.py
```

### 8.4 성능 최적화
```bash
# 데이터베이스 최적화
python -c "import sqlite3; conn=sqlite3.connect('data/velos.db'); conn.execute('VACUUM'); conn.close()"

# 메모리 정리
python -c "import gc; gc.collect()"
```

---

## 부록

### A. 유용한 명령어 모음
```bash
# 시스템 상태 확인
python scripts/preflight_verify.py

# 메모리 요약 생성
python scripts/generate_memory_summary.py

# 리플렉션 정규화
python scripts/normalize_reflections.py

# API 비용 요약
python scripts/api_cost_rollup.py
```

### B. 로그 레벨 설정
```python
# configs/settings.yaml에 추가
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file_rotation: true
  max_size: 10MB
```

### C. 알림 설정
```python
# Slack 알림 설정
notifications:
  slack:
    enabled: true
    channel: "#velos-alerts"
    level: WARNING  # ERROR만 알림
  
  email:
    enabled: false
    recipients: ["admin@example.com"]
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
