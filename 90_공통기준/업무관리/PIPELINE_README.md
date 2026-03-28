# 자동화 동기화 파이프라인 가이드

## 구성 파일

| 파일 | 역할 |
|------|------|
| `watch_changes.py` | Phase 1 — 파일 변경 감지 엔진 (메인 실행 파일) |
| `auto_watch_config.yaml` | 감시 루트, debounce 30분, 제외 패턴 설정 |
| `commit_docs.py` | Phase 2 — Git 자동 커밋 |
| `auto_commit_config.yaml` | allowlist / blocklist / 커밋 메시지 규칙 |
| `update_status_tasks.py` | Phase 3 — 로컬 STATUS.md / TASKS.md 자동 갱신 |
| `status_rules.yaml` | meaningful / skip 패턴 정의 |
| `slack_notify.py` | Phase 4 — Slack 배치 완료 알림 |
| `slack_config.yaml` | 채널 ID, 알림 조건, 핵심 파일 패턴 |
| `notion_sync.py` | Phase 5 — Notion 페이지 자동 동기화 |
| `notion_config.yaml` | 페이지 ID, 토큰 경로, 동기화 조건 |
| `watch_changes_launcher.vbs` | 콘솔 없이 watch_changes.py 백그라운드 실행 |
| `register_watch_task.bat` | 작업 스케줄러 등록 (재시작 옵션 포함) |
| `watch_task.xml` | 작업 스케줄러 XML 정의 |

---

## 훅 체인

```
파일 변경 감지 (30분 idle debounce)
  └─ Phase 1: JSONL 로그 기록
  └─ Phase 3: 로컬 STATUS.md / TASKS.md 자동 갱신
  └─ Phase 2: Git 자동 커밋 (allowlist 기준)
  └─ Phase 4: Slack 알림 (#새-워크스페이스-전체)
  └─ Phase 5: Notion 페이지 동기화
```

---

## 실행 방법

```bash
# 일반 실행
python watch_changes.py

# 테스트 (로그/커밋/알림 없이 콘솔 출력만)
python watch_changes.py --dry-run
```

---

## 상시 실행 설정

**현재 적용:** Startup 폴더 — 로그인 시 자동 시작
```
C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
watch_changes_launcher.vbs
```

**재시작 옵션 적용:** CMD에서 `register_watch_task.bat` 직접 실행

---

## 토큰 위치

| 서비스 | 환경변수 | fallback 경로 |
|--------|---------|--------------|
| Slack | `SLACK_BOT_TOKEN` | `C:/Users/User/Desktop/gpt설정api/.env` |
| Notion | `NOTION_TOKEN` | `C:/Users/User/Desktop/gpt설정api/.env` |

---

## 초기 설정 (미완료 항목)

1. **Notion 통합 앱 연결** — `📁 업무리스트 운영` 페이지 → `...` → 연결 → `GPT 자동 분류 시스템`
2. **Slack Bot Token 갱신** — api.slack.com → 앱 → OAuth & Permissions → 재발급 후 `.env` 교체
3. **작업 스케줄러 등록** — CMD에서 `register_watch_task.bat` 실행
