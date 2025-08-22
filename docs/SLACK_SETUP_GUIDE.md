# 🚀 VELOS Slack 통합 설정 가이드

## 📋 설정 단계별 가이드

### 1️⃣ Slack App 생성 및 Bot Token 발급

#### Slack App 생성
1. [Slack API](https://api.slack.com/apps) 접속
2. **"Create New App"** 클릭
3. **"From scratch"** 선택
4. App 이름 입력 (예: "VELOS Bot")
5. 워크스페이스 선택

#### Bot Token 권한 설정
**OAuth & Permissions** 페이지에서 다음 권한 추가:
```
Bot Token Scopes:
- chat:write          # 메시지 전송
- files:write         # 파일 업로드  
- files:read          # 파일 읽기
- channels:read       # 채널 정보 읽기
- groups:read         # 그룹 정보 읽기
- im:read            # DM 읽기
- im:write           # DM 쓰기
- users:read         # 사용자 정보 읽기
```

#### Bot Token 복사
**OAuth & Permissions** → **Bot User OAuth Token** (`xoxb-`로 시작)

### 2️⃣ 채널 ID 확인

#### 방법 1: 웹에서 확인
1. Slack 웹 앱에서 원하는 채널 접속
2. URL에서 채널 ID 확인: `https://app.slack.com/client/T.../C12345678901`
3. `C12345678901` 부분이 채널 ID

#### 방법 2: 앱에서 확인  
1. 채널 우클릭 → **Copy link**
2. 링크에서 채널 ID 추출

#### DM 채널의 경우
- 사용자 ID(`U`로 시작)를 입력하면 자동으로 DM 채널로 변환됩니다.

### 3️⃣ 환경 변수 설정

`/home/user/webapp/configs/.env` 파일 수정:

```bash
# 필수 설정
SLACK_BOT_TOKEN=xoxb-XXXX-XXXX-XXXX-YOUR-ACTUAL-TOKEN
SLACK_CHANNEL_ID=C1234567890

# 선택 설정  
DISPATCH_SLACK=1
```

### 4️⃣ 봇을 채널에 초대

1. 대상 채널에서 `/invite @VELOS Bot` 실행
2. 또는 채널 멤버 추가에서 봇 검색 후 추가

### 5️⃣ 테스트 실행

```bash
# 기본 테스트
cd /home/user/webapp
python scripts/test_slack_integration.py

# 파일 업로드 테스트  
python scripts/notify_slack_api.py

# Bridge 시스템 테스트
python scripts/velos_bridge.py
```

## 🔧 고급 설정

### Webhook URL 사용 (선택사항)
Bot Token 대신 Webhook URL 사용:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
```

### 다중 채널 설정
```bash  
SLACK_CHANNEL=C1234567890          # 메인 채널
SLACK_SUMMARY_CH=C0987654321       # 요약 채널
```

### 환경별 설정
```bash
DEBUG=1                           # 디버그 모드
LOG_LEVEL=DEBUG                   # 로그 레벨
```

## ⚠️ 문제 해결

### 일반적인 오류들

#### `account_inactive`
- Bot Token이 비활성화됨
- 새 Token 재발급 필요

#### `channel_not_found`  
- 채널 ID가 잘못되었거나
- 봇이 채널에 초대되지 않음

#### `missing_scope`
- Bot 권한 부족
- OAuth Permissions에서 권한 추가 후 재설치

#### `token_revoked`
- Token이 취소됨  
- 새 Token 발급 및 재설정

### 디버깅 방법
```bash
# 로그 확인
tail -f /home/user/webapp/logs/velos_bridge.log

# 전송 결과 확인
ls -la /home/user/webapp/data/reports/_dispatch_processed/

# 실패 기록 확인
ls -la /home/user/webapp/data/reports/_dispatch_failed/
```

## 📊 사용법

### 수동 메시지 전송
```python
from scripts.notify_slack_api import send_text, CHANNEL_ID
send_text(CHANNEL_ID, "테스트 메시지")
```

### 파일 업로드
```python  
from scripts.notify_slack_api import send_report
from pathlib import Path

file_path = Path("report.pdf")
send_report(file_path, title="VELOS Report", comment="보고서입니다")
```

### Bridge 시스템 사용
JSON 파일을 큐에 넣어 자동 전송:
```json
{
  "title": "VELOS 알림",
  "message": "시스템 상태 업데이트",
  "channels": {
    "slack": {
      "enabled": true,
      "channel": "#general"
    }
  }
}
```

이 가이드를 따라 설정하면 VELOS Slack 통합 기능을 완전히 활용할 수 있습니다! 🎉