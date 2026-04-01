# Local Hooks 강제 명세 (Contract)

> 이 문서는 Git 추적 대상이다. `.claude/` 하위 로컬 전용 hooks의 **명세 원본**이다.
> hooks 코드 자체는 `.gitignore`이므로 이 명세로 존재·규칙·상태를 검증한다.
> 최종 갱신: 2026-04-01

---

## 1. 필수 Hook 스크립트 목록

| # | 파일명 | 이벤트 | matcher | 목적 |
|---|--------|--------|---------|------|
| 1 | `pre_write_guard.sh` | PreToolUse | `Edit\|Write\|Bash` | plan.md 없는 구현 수정 차단 |
| 2 | `post_write_dirty.sh` | PostToolUse | `Edit\|Write\|Bash` | 파일 변경 시 dirty.flag 생성 |
| 3 | `pre_finish_guard.sh` | Stop | (전체) | dirty.flag 존재 + verify.json PASS 없으면 완료 차단 |
| 4 | `gpt_followup_guard.sh` | PostToolUse + Stop | `mcp__Claude_in_Chrome\|Bash\|Edit\|Write` | GPT 응답 읽기 후 후속작업 없이 종료 차단 |

### 기존 hooks (1단계 이전부터 존재)

| # | 파일명 | 이벤트 | matcher | 목적 |
|---|--------|--------|---------|------|
| 5 | `block_dangerous.sh` | PreToolUse | `Bash` | 위험 명령 차단 |
| 6 | `protect_files.sh` | PreToolUse | `Write\|Edit\|MultiEdit` | 보호 파일 수정 차단 |
| 7 | `domain_guard.sh` | PreToolUse | `mcp__Claude_in_Chrome` | 도메인 접근 제어 |
| 8 | `post_validate.sh` | PostToolUse | `Write\|Edit\|MultiEdit` | 수정 후 검증 |
| 9 | `domain_read_tracker.sh` | PostToolUse | `Read` | 도메인 문서 읽기 추적 |
| 10 | `notify_slack.sh` | Notification | (전체) | Slack 알림 |
| 11 | `stop_guard.sh` | Stop | (전체) | 금지 문구 차단 |
| 12 | `session_start.sh` | SessionStart | (전체) | 세션 초기화 |
| 13 | `prompt_inject.sh` | UserPromptSubmit | (전체) | 체크리스트 주입 |

---

## 2. settings.local.json 등록 규칙

- 파일 위치: `.claude/settings.local.json`
- 총 hook 등록 수: **19개** (PreToolUse 4 + PostToolUse 4 + Notification 1 + Stop 3 + SessionStart 1 + UserPromptSubmit 1 + 기타 중복 등록 5)
- **기존 hook 삭제 금지** — 신규 hook은 append 방식으로만 추가
- matcher는 필요 최소 범위로 지정 (전체 `.*` 금지 원칙)

### 이벤트별 등록 현황

```
PreToolUse:
  [0] Bash → block_dangerous.sh
  [1] Write|Edit|MultiEdit → protect_files.sh
  [2] mcp__Claude_in_Chrome → domain_guard.sh
  [3] Edit|Write|Bash → pre_write_guard.sh          ← 1단계

PostToolUse:
  [0] Write|Edit|MultiEdit → post_validate.sh
  [1] Read → domain_read_tracker.sh
  [2] Edit|Write|Bash → post_write_dirty.sh          ← 1단계
  [3] mcp__Claude_in_Chrome|Bash|Edit|Write → gpt_followup_guard.sh  ← 1단계

Notification:
  [0] (전체) → notify_slack.sh

Stop:
  [0] (전체) → stop_guard.sh
  [1] (전체) → pre_finish_guard.sh                   ← 1단계
  [2] (전체) → gpt_followup_guard.sh                 ← 1단계

SessionStart:
  [0] (전체) → session_start.sh

UserPromptSubmit:
  [0] (전체) → prompt_inject.sh
```

---

## 3. 상태 파일 (State)

| 파일 | 위치 | 생성 주체 | 소비 주체 | 의미 |
|------|------|----------|----------|------|
| `current_task` | `agent-control/state/` | Claude (수동) | pre_write_guard, pre_finish_guard | 현재 작업 디렉토리 경로 |
| `dirty.flag` | `agent-control/state/` | post_write_dirty.sh | pre_finish_guard.sh | 검증 필요한 파일 변경 발생 |
| `gpt_followup_pending.flag` | `agent-control/state/` | gpt_followup_guard.sh | gpt_followup_guard.sh (Stop) | GPT 응답 읽기 후 후속작업 미완료 |

### 상태 파일 Git 추적 규칙

- `agent-control/state/` **디렉토리 구조만** Git 추적 (`.gitkeep`)
- `current_task`, `dirty.flag`, `gpt_followup_pending.flag` 실제 파일은 **`.gitignore` 대상**
- 이유: 세션/머신 종속 런타임 산출물이므로 커밋 시 세션 간 오염, false positive, 커밋 노이즈 발생
- smoke_test.sh는 "파일 존재 여부"가 아니라 "hook이 해당 파일을 기대 위치에서 참조하는지"를 검증

---

## 4. 차단 조건 요약

### pre_write_guard.sh (진입 게이트)
- `current_task` 설정됨 + `plan.md` 없음 → **DENY**
- `plan.md` 존재 + `approved: true` 없음 → **DENY**
- `plan.md` 승인됨 + 대상 파일이 `files_to_change`에 없음 → **DENY**
- EXEMPT: request.md, research.md, plan.md, verify.json, HANDOFF.md, TASKS.md, STATUS.md, CLAUDE.md, `.claude/hooks/*`

### post_write_dirty.sh (변경 추적)
- Edit/Write: EXEMPT가 아닌 파일 수정 시 → `dirty.flag` 생성
- Bash: mutating 패턴(cp, mv, rm, python+openpyxl 등) 감지 시 → `dirty.flag` 생성
- EXEMPT 동일

### pre_finish_guard.sh (완료 게이트)
- `dirty.flag` 존재 + 완료 보고 패턴 + `verify.json` 없음 → **BLOCK**
- `verify.json` 존재 + `status ≠ pass` → **BLOCK**
- `verify.json` mtime < `dirty.flag` mtime → **BLOCK** (재검증 필요)
- `verify_required: true`가 plan.md에 없으면 통과

### gpt_followup_guard.sh (GPT 후속작업 강제)
- PostToolUse: GPT 응답 읽기 감지 → `pending.flag` 생성
- PostToolUse: 전송/후속작업 감지 → `pending.flag` 삭제
- Stop: `pending.flag` 존재 + 예외 아님 → **BLOCK**
- 예외: timeout, 타임아웃, 로그인 만료, 네트워크 오류, 검토만, 읽기만, 예외 종료

---

## 5. EXEMPT 파일 목록 (공통)

pre_write_guard.sh와 post_write_dirty.sh가 공유하는 EXEMPT 목록:

```
request.md, research.md, plan.md, verify.json,
HANDOFF.md, TASKS.md, STATUS.md, CLAUDE.md,
.claude/hooks/*
```

EXEMPT 파일은 plan.md 없이도 수정 가능하고, dirty.flag를 트리거하지 않는다.

---

## 6. smoke_test.sh 검증 계약

smoke_test.sh는 아래 항목을 최소한 PASS해야 한다:

### 기존 4묶음 (10개)
1. stop_guard.sh 존재 + 실행 가능 + 금지 패턴 + BLOCK 로깅 + python3 파싱
2. prompt_inject.sh 존재 + 실행 가능 + 토론모드 키워드
3. post_validate.sh 존재 + 실행 가능 + find() 충돌 + polling 불일치
4. session_start.sh 존재 + 실행 가능

### 1단계 추가 (8개)
5. pre_write_guard.sh 존재 + 실행 가능 + EXEMPT 정의 + plan.md 파싱
6. post_write_dirty.sh 존재 + 실행 가능 + dirty.flag 생성 로직
7. pre_finish_guard.sh 존재 + 실행 가능 + verify.json 검사 로직
8. gpt_followup_guard.sh 존재 + 실행 가능 + pending.flag 상태기계

총 **18개 테스트 케이스**.
