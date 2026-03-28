# slack_notify.py 가이드

## 동작 위치

Phase 1 flush → Phase 3 → Phase 2 → **Phase 4 (Slack 알림)**

Phase 2 커밋 결과까지 집계 후, 배치 단위로 Slack 채널에 1회 알림.

---

## 알림 조건

| 조건 | 설정 키 | 기본값 |
|------|---------|--------|
| STATUS/TASKS 갱신 성공 | `notify_on.status_tasks_updated` | true |
| STATUS/TASKS 갱신 실패 | `notify_on.status_tasks_failed` | true |
| Git 커밋 성공 | `notify_on.git_commit_success` | true |
| Git 커밋 실패 | `notify_on.git_commit_failed` | true |
| 핵심 파일 변경 포함 | `notify_on.critical_file_changed` | true |

> 위 조건 중 하나도 해당 없으면 알림 미발송.

---

## 핵심 파일 패턴

`slack_config.yaml` 의 `critical_patterns` 목록에 해당하는 파일이 배치에 포함되면 무조건 알림.

기본값: `CLAUDE.md`, `*.skill`, `auto_watch_config.yaml`, `auto_commit_config.yaml`, `status_rules.yaml`

---

## 토큰 설정

우선순위:
1. 환경변수 `SLACK_BOT_TOKEN`
2. `C:/Users/User/Desktop/gpt파일api/.env` 파일 내 `SLACK_BOT_TOKEN=...`

채널: `C096LU8PH44` (#새-워크스페이스-전체)

> **주의**: `.env` 파일의 토큰이 `account_inactive` 상태면 알림이 발송되지 않고 조용히 건너뜀.
> 토큰 갱신 방법:
> 1. https://api.slack.com/apps → 앱 선택 → OAuth & Permissions
> 2. Bot Token Scopes: `chat:write`, `chat:write.public`
> 3. Install to Workspace → Bot User OAuth Token 복사
> 4. `.env` 파일의 `SLACK_BOT_TOKEN=` 값 교체

---

## 실행 방법

### dry-run (실제 발송 없이 콘솔 출력)
```bash
python slack_notify.py --dry-run
```

### 테스트 메시지 직접 발송
```bash
python slack_notify.py --message "테스트 알림"
```

### watch_changes.py 기동 시 자동 연결
```bash
python watch_changes.py
```

---

## 중복 방지

- `batch_id` 기반 dedup
- 동일 batch_id 는 `dedup_window_hours`(기본 1시간) 이내 재발송 없음
- 상태 파일: `.slack_dedup_state.json`

---

## 메시지 예시

```
*업무리스트 AutoBot* | 2026-03-28 14:35 | 배치 a1b2c3d4
파일 3건 처리
[핵심 파일 변경] CLAUDE.md
[STATUS/TASKS 갱신] STATUS.md, TASKS.md
[Git 커밋] 3건 커밋 (abc1234)
```

---

## 오류 로그

`slack_errors_YYYYMMDD.log` — 발송 실패 시 기록, 원본 흐름은 계속 진행
