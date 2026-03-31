# 업무 자동화 에이전트 가이드

> 이 문서는 프로젝트의 자동화 구성요소를 6계층으로 정리한 운영 맵이다.
> 새 세션 시작 시 전체 구조를 파악하는 참조 문서로 사용한다.

---

## 아키텍처 개요

```
현업 계층  →  상태 계층  →  협업 계층  →  검증 계층  →  실행 계층  →  감시 계층
```

---

## 1. 현업 계층

현업 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본.

| 구성요소 | 경로 |
|---------|------|
| 업무 마스터리스트 | `90_공통기준/업무관리/업무_마스터리스트.xlsx` |

AI 작업의 원본이 아님. 현업 업무 질문은 이 파일을 먼저 확인.

---

## 2. 상태 계층

AI 작업 상태의 원본. 판정 우선순위: TASKS > STATUS > HANDOFF > Notion

| 구성요소 | 경로 | 역할 |
|---------|------|------|
| TASKS.md | `90_공통기준/업무관리/TASKS.md` | 상태 원본 (1순위) |
| STATUS.md | `90_공통기준/업무관리/STATUS.md` | 운영 요약, 재개 위치 |
| HANDOFF.md | `90_공통기준/업무관리/HANDOFF.md` | 세션 인수인계 메모 |
| 도메인 STATUS | `05_생산실적/조립비정산/STATUS.md` 등 | 도메인별 재개 위치 |

---

## 3. 협업 계층

Claude-GPT 공동작업 + 운영 원칙.

| 구성요소 | 역할 |
|---------|------|
| CLAUDE.md (루트) | 프로젝트 전체 운영 원칙 |
| 도메인 CLAUDE.md | 업무별 세부 규칙 |
| Plan-First 워크플로우 | research.md → plan.md 승인 → 구현 |
| GPT 공동작업 | 작업 완료 → push → GPT 검증 → PASS/FAIL |

---

## 4. 검증 계층

자동/반자동 품질 검증 체계.

### Hooks (.claude/hooks/)

| 스크립트 | 이벤트 | 역할 |
|---------|--------|------|
| block_dangerous.sh | PreToolUse(Bash) | 위험 명령 차단 |
| protect_files.sh | PreToolUse(Write/Edit) | 보호 파일 deny/log |
| notify_slack.sh | Notification | Slack 알림 (60초 dedup) |
| session_start.sh | SessionStart | 인수인계 읽기 순서 리마인드 |
| session_end.sh | SessionEnd | HANDOFF 갱신 리마인드 |
| instructions_loaded.sh | InstructionsLoaded | CLAUDE.md 로드 로그 |
| skill_config_change.sh | ConfigChange | 설정 변경 감지 로그 |

### Commands (.claude/commands/)

| 커맨드 | subagent 역할 |
|--------|-------------|
| /doc-check | 문서 정합성 검사 (TASKS/STATUS/HANDOFF 충돌) |
| /task-status-sync | 상태 충돌 탐지 (패턴 A~D) |
| /review-claude-md | CLAUDE.md 규칙 검토 |

### 하네스 3인 체제

| 역할 | 담당 |
|------|------|
| Planner | 작업 범위와 기준 정리 |
| Generator | 기준에 따라 결과물 생성/수정 |
| Evaluator | 결과물을 기준표에 따라 판정 |

---

## 5. 실행 계층

반복 업무 자동화 스킬 + 스크립트.

| 스킬 | 용도 |
|------|------|
| line-batch-management | ERP 라인배치 입력 |
| line-batch-mainsub | 메인서브 품번 배치 |
| assembly-cost-settlement | 조립비 정산 |
| zdm-daily-inspection | ZDM 일상점검 |
| mes-production-upload | MES 생산실적 업로드 |
| xlsx/docx/pdf/pptx | 파일 형식별 처리 |
| youtube-analysis | YouTube 영상 분석 |

---

## 6. 감시 계층

외부 파일 변경 감지 → 자동 커밋/상태갱신/알림 체인.

| Phase | 스크립트 | 역할 |
|-------|---------|------|
| 1 | watch_changes.py | 파일 변경 감지 (watchdog) + debounce 30분 |
| 2 | commit_docs.py | allowlist 기준 git add/commit/push |
| 3 | update_status_tasks.py | STATUS.md/TASKS.md 자동 갱신 |
| 4 | slack_notify.py | Slack 알림 발송 |
| 5 | notion_sync.py | Notion 현황판 동기화 |
| 6 | skill_install.py | .skill 파일 변경 시 자동 설치 |

---

## 세션 시작 체크리스트

1. TASKS.md 읽기 (상태 원본)
2. STATUS.md 읽기 (재개 위치)
3. HANDOFF.md 읽기 (세션 메모)
4. `/doc-check` 실행 (정합성 사전 확인 권장)
5. 현업 질문이면 `업무_마스터리스트.xlsx` 먼저
