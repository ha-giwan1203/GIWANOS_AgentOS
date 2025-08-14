# velos_bridge.py

## 개요

VELOS 브릿지 시스템은 외부 서비스(Slack, Notion)와의 연동을 담당하는 핵심 컴포넌트입니다. 디스패치 대기열에서 티켓을 읽어 처리하고, 성공/실패에 따라 적절한 디렉토리로 이동시킵니다.

**위치**: `scripts/velos_bridge.py`

## 주요 기능

1. **디스패치 큐 모니터링**: 두 개의 대기열을 지속적으로 모니터링
2. **외부 서비스 연동**: Slack, Notion API를 통한 메시지/파일 전송
3. **오류 처리**: 전송 실패 시 적절한 오류 처리 및 로깅
4. **파일 관리**: 처리된 티켓을 성공/실패 디렉토리로 분류

## 시스템 아키텍처

### 대기열 구조
```
data/dispatch/_queue/          # 일반 디스패치 대기열
data/reports/_dispatch/        # 보고서 디스패치 대기열
```

### 처리 결과 디렉토리
```
data/dispatch/_processed/      # 성공 처리된 파일
data/dispatch/_failed/         # 실패 처리된 파일
data/reports/_dispatch_processed/  # 성공 처리된 보고서
data/reports/_dispatch_failed/     # 실패 처리된 보고서
```

## 코드 구조

### 핵심 설정
```python
INBOXES = [
    ROOT / "data" / "dispatch" / "_queue",
    ROOT / "data" / "reports" / "_dispatch",
]

OUTS = {
    str(ROOT / "data" / "dispatch" / "_queue"): (
        ROOT / "data" / "dispatch" / "_processed",
        ROOT / "data" / "dispatch" / "_failed",
    ),
    str(ROOT / "data" / "reports" / "_dispatch"): (
        ROOT / "data" / "reports" / "_dispatch_processed",
        ROOT / "data" / "reports" / "_dispatch_failed",
    ),
}
```

### 로깅 시스템
```python
def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)
```

## 주요 함수

### send_slack()
**목적**: Slack으로 메시지 전송

**매개변수**:
- `text` (str): 전송할 텍스트
- `channel` (str): 채널 ID (기본값: None)

**반환값**:
- `True`: 전송 성공
- `False`: 전송 실패
- `None`: 전송 시도 불가 (SKIP)

**동작 방식**:
1. `slack_api` 모듈 우선 시도
2. 실패 시 `slack_legacy` 모듈 시도
3. 둘 다 실패 시 SKIP 처리

### send_notion()
**목적**: Notion으로 페이지 전송

**매개변수**:
- `title` (str): 페이지 제목
- `md_content` (str): 마크다운 내용 (선택사항)
- `parent_id` (str): 부모 페이지 ID

**반환값**:
- `True`: 전송 성공
- `False`: 전송 실패
- `None`: 전송 시도 불가 (SKIP)

### process_ticket()
**목적**: 디스패치 티켓 처리

**매개변수**:
- `p` (Path): 처리할 티켓 파일 경로

**반환값**:
- `True`: 처리 성공
- `False`: 처리 실패

**처리 로직**:
1. JSON 파일 읽기 (BOM 안전)
2. Slack/Notion 채널 설정 확인
3. 각 채널별 전송 시도
4. 성공/실패 판정

### handle_file()
**목적**: 개별 파일 처리 및 이동

**매개변수**:
- `p` (Path): 처리할 파일 경로

**동작 방식**:
1. `process_ticket()` 호출
2. 결과에 따라 성공/실패 디렉토리로 이동
3. 예외 발생 시 실패 디렉토리로 이동

## 티켓 형식

### 기본 티켓 구조
```json
{
  "id": "uuid-string",
  "created_utc": "20250814_064536",
  "title": "제목",
  "message": "메시지 내용",
  "report_md": "마크다운 내용",
  "channels": {
    "slack": {
      "enabled": true,
      "channel": "#general"
    },
    "notion": {
      "enabled": true,
      "parent_page_id": "page-id"
    }
  }
}
```

### 채널 설정
```json
{
  "slack": {
    "enabled": true,
    "channel": "#channel-name"
  },
  "notion": {
    "enabled": true,
    "parent_page_id": "page-id",
    "database_id": "database-id"
  }
}
```

## 실행 방법

### 기본 실행
```bash
python scripts/velos_bridge.py
```

### 스케줄링 실행 (5분마다)
```bash
# crontab 설정
*/5 * * * * cd /path/to/giwanos && python scripts/velos_bridge.py
```

### Windows 작업 스케줄러
```powershell
schtasks /create /tn "VELOS_Bridge" /tr "python C:\giwanos\scripts\velos_bridge.py" /sc minute /mo 5
```

## 환경변수 설정

### 필수 환경변수
```env
# Slack 설정
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C0123456789

# Notion 설정
NOTION_TOKEN=secret-your-notion-token
```

### 선택적 환경변수
```env
# 대체 Slack 토큰
SLACK_TOKEN=xoxb-alternative-token
```

## 오류 처리

### 오류 분류
1. **전송 성공**: 1개 이상의 채널에서 성공
2. **전송 실패**: 모든 시도한 채널에서 실패
3. **전송 SKIP**: 전송 시도 자체가 불가능한 경우

### 판정 로직
```python
# 판정: 성공 1개 이상이면 OK, 시도 자체가 없었으면 OK, 그 외(모두 실패) FAILED
if success >= 1:
    return True
if attempted == 0:
    return True
return False
```

### 로그 예시
```
[2025-08-14 15:46:27] 처리 시작: dispatch_20250814_064536.json @ C:\giwanos\data\reports\_dispatch
[2025-08-14 15:46:28] Slack 실패: invalid_auth
[2025-08-14 15:46:29] Notion 실패: invalid_token
[2025-08-14 15:46:29] 처리 결과: dispatch_20250814_064536.json -> FAILED
```

## 성능 최적화

### 처리 최적화
1. **파일 정렬**: `sorted()` 함수로 처리 순서 보장
2. **배치 처리**: 여러 파일을 한 번에 처리 가능
3. **비동기 처리**: 향후 비동기 전송 고려

### 메모리 최적화
1. **파일 스트리밍**: 대용량 파일 처리 시 스트리밍 방식 사용
2. **가비지 컬렉션**: 처리 후 메모리 정리
3. **연결 풀링**: API 연결 재사용

## 모니터링

### 로그 모니터링
```bash
# 실시간 로그 확인
tail -f data/logs/velos_bridge.log

# 오류 로그 필터링
grep "FAILED" data/logs/velos_bridge.log
```

### 성능 모니터링
```bash
# 처리 시간 측정
time python scripts/velos_bridge.py

# 큐 상태 확인
ls -la data/reports/_dispatch/
ls -la data/dispatch/_queue/
```

## 확장 가능성

### 새로운 채널 추가
```python
def send_new_channel(text, config):
    # 새로운 채널 구현
    pass

# process_ticket() 함수에 추가
if new_channel.get("enabled"):
    r = send_new_channel(text, new_channel)
    if r is True: success += 1
    if r is False: attempted += 1
```

### 플러그인 시스템
```python
# 향후 플러그인 구조 도입 가능
plugins = load_channel_plugins()
for plugin in plugins:
    if plugin.is_enabled(ticket):
        result = plugin.send(ticket)
```

## 테스트

### 단위 테스트
```python
def test_send_slack():
    # Slack 전송 테스트
    pass

def test_send_notion():
    # Notion 전송 테스트
    pass

def test_process_ticket():
    # 티켓 처리 테스트
    pass
```

### 통합 테스트
```python
def test_full_bridge_workflow():
    # 전체 브릿지 워크플로우 테스트
    pass
```

## 주의사항

1. **BOM 안전**: UTF-8 with/without BOM 모두 지원
2. **파일 이동**: `shutil.move()` 사용으로 원자적 이동
3. **예외 처리**: 모든 예외를 캐치하여 로그 기록
4. **토큰 보안**: 환경변수로 API 토큰 관리

## 관련 파일

- `scripts/run_giwanos_master_loop.py`: 디스패치 티켓 생성
- `scripts/notify_slack_api.py`: Slack API 연동
- `tools/notion_integration/`: Notion API 연동
- `data/logs/velos_bridge.log`: 브릿지 로그

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
