# 업무리스트 작업 목록

최종 업데이트: 2026-03-28 (line-batch-management.skill 패키지화 완료 — v7→v9 기준 전환)

---

## 진행 중

없음

---

## 대기 중 (우선순위 순)

### [중] 보류 판정 유지 1건 후속 조치

| 파일 | 조치 내용 | 기준 문서 |
|------|----------|----------|
| `ENDPART라인배정(partLineBatchmL) (260324).xlsx` | 라인배치 기준 변경 시 갱신 기준 확인 | `03_품번관리\초물관리\` |

### [낮] 파일 정리 2차
- `99_임시수집` 내 미분류 파일 카테고리 배치
- 각 도메인 내 신규 수집 파일 정기 점검

### [낮] Slack Bot Token 갱신 (사용자 직접)
- 현재 `.env` 파일의 `SLACK_BOT_TOKEN` — `account_inactive` 상태
- https://api.slack.com/apps → 앱 선택 → OAuth & Permissions → Bot Token Scopes: `chat:write` → Reinstall
- 새 토큰을 `C:/Users/User/Desktop/gpt파일api/.env`의 `SLACK_BOT_TOKEN=` 값에 교체
- 갱신 후 `python slack_notify.py --message "토큰 갱신 테스트"` 실행

### [낮] 작업 스케줄러 등록 (사용자 직접 — 재시작 옵션 적용)
- CMD 열고 실행: `C:\Users\User\Desktop\업무리스트\90_공통기준\업무관리\register_watch_task.bat`
- 현재는 Startup 폴더 방식으로 자동 시작되나, 재시작 옵션 없음
- 스케줄러 등록 시 실패 후 1분 간격 3회 재시작 적용됨

### [낮] 도메인 STATUS.md 점검
- `05_생산실적\조립비정산\STATUS.md` — 마이그레이션 이후 경로 반영 확인
- `10_라인배치\STATUS.md` — 현행 기준 반영 확인

---

## 완료됨

| 항목 | 완료일 |
|------|--------|
| 폴더 마이그레이션 Phase 0~7 | 2026-03-28 |
| 파일 정리 1차 (94건 아카이브) | 2026-03-28 |
| 커넥터 운영 지침 v1.0 확정 | 2026-03-28 |
| 보호 파일 10건 목록 고정 | 2026-03-28 |
| 보류 파일 5건 최종 판정 | 2026-03-28 |
| CLAUDE.md 전면 개정 (1차) | 2026-03-28 |
| __pycache__ 삭제 | 2026-03-28 |
| Notion 업무 현황 페이지 생성 | 2026-03-28 |
| Slack 완료 보고 발송 | 2026-03-28 |
| Google Calendar 후속 작업 4건 등록 | 2026-03-28 |
| GitHub 운영 문서 push (PR #8) | 2026-03-28 |
| GitHub PR #8 머지 (main 반영) | 2026-03-28 |
| 자동화 동기화 Phase 1 (watch_changes.py) | 2026-03-28 |
| 자동화 동기화 Phase 2 (commit_docs.py) | 2026-03-28 |
| 자동화 동기화 Phase 3 (update_status_tasks.py) | 2026-03-28 |
| 자동화 동기화 Phase 4 (slack_notify.py) | 2026-03-28 |
| Slack 채널 연결 테스트 (MCP 경유) | 2026-03-28 |
| watch_changes.py Startup 폴더 상시 실행 등록 | 2026-03-28 |
| 작업 스케줄러 등록 파일 작성 (bat/xml) | 2026-03-28 |
| 폴더 생성 규칙 메모리 저장 | 2026-03-28 |
| 커넥터 운영구조 재정의 (Drive/GitHub/Notion 역할 확정) | 2026-03-28 |
| CLAUDE.md 2차 개정 (파일명규칙·환경설정 삭제, AI 인수인계 추가) | 2026-03-28 |
| 운영지침_커넥터관리_v1.0.md v1.1 갱신 | 2026-03-28 |
| README.md 신규 생성 (루트 AI 세션 진입점) | 2026-03-28 |
| HANDOFF.md 신규 생성 (AI 인수인계 문서 체계) | 2026-03-28 |
| GitHub PR #9 생성 및 main 머지 | 2026-03-28 |
| 조립비정산 데이터사전 동기화 (데이터사전 v1.0 + pipeline_contract.md + CLAUDE.md) | 2026-03-28 |
| line-batch-management.skill 패키지화 (v7→v9 기준 전환, SNAP-ON/LASER MARKING 갱신) | 2026-03-28 |
