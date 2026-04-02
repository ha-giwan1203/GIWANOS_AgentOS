# Hooks 층 표준화

> GPT+Claude 합의 2026-04-02 (하네스 영상 분석 → smoke_test 확대 → 층 표준화)
> 훅 추가/수정 시 이 분류를 참조하여 적절한 층에 배치한다.

## 감지층 (Detection) — 상태 변화 인식, 플래그 생성

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `post_write_dirty.sh` | PostToolUse(Edit/Write/Bash) | 파일 변경 시 dirty.flag 타임스탬프 기록 |
| `domain_read_tracker.sh` | PostToolUse(Read) | 도메인 CLAUDE.md 읽기 완료 시 loaded 플래그 생성 |
| `prompt_inject.sh` | UserPromptSubmit | 도메인 키워드 감지 → active 플래그 + 체크리스트 주입 |

## 차단층 (Blocking) — 규칙 위반 시 실행 차단

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `domain_guard.sh` | PreToolUse(mcp__Claude_in_Chrome) | 도메인 활성 + 미로드 시 Read(CLAUDE.md) 외 전도구 차단 |
| `block_dangerous.sh` | PreToolUse(Bash) | 위험 bash 명령 차단 (rm -rf, git reset --hard 등) |
| `protect_files.sh` | PreToolUse(Write/Edit/MultiEdit) | 보호 대상 파일 수정 차단 |
| `pre_write_guard.sh` | PreToolUse(Edit/Write/Bash) | plan.md 미승인 시 구현 파일 수정 차단 |
| `stop_guard.sh` | Stop | 금지 문구(채택/버림 누락) 포함 시 Stop 차단 |
| `completion_gate.sh` | Stop | TASKS/HANDOFF 미갱신 시 Stop 차단 |
| `cleanup_audit.sh` | Stop | untracked 파일 미정리 시 Stop 차단 |
| `pre_finish_guard.sh` | Stop | verify.json 미완 시 Stop 차단 |
| `gpt_followup_guard.sh` | Stop + PostToolUse | GPT 후속작업 미처리 시 차단 |

## 정리층 (Maintenance) — 자동 검증·변환

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `post_validate.sh` | PostToolUse(Write/Edit/MultiEdit) | CLAUDE.md 내부 모순 자동 감지 |
| `auto_compile.sh` | PostToolUse(Write/Edit) | 파일 수정 후 자동 컴파일/변환 |

## 알림층 (Notification) — 외부 알림

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `notify_slack.sh` | Notification (async) | Slack 채널 알림 발송 |

## 감사층 (Audit) — 이력 기록·분석

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `bash_audit_log.sh` | PostToolUse(Bash) | Bash 명령 실행 이력 로깅 |
| `subagent_audit_log.sh` | SubagentStart/SubagentStop (async) | subagent 시작/종료 이력 로깅 |
| `post_tool_failure.sh` | PostToolUseFailure | 도구 실패 시 로깅 |

## 세션 관리 (Session) — 세션 생명주기

| 훅 | 이벤트 | 역할 |
|---|---|---|
| `session_start.sh` | SessionStart | 세션 시작 시 초기화 |
| `session_preflight.sh` | SessionStart | 세션 시작 시 사전 점검 |
| `pre_compact.sh` | PreCompact | 컨텍스트 압축 전 저장 |

## 미연결·보조 — settings.local.json에 미등록 (수동 실행 또는 예비)

| 스크립트 | 상태 | 비고 |
|---|---|---|
| `session_end.sh` | 미연결 | SessionEnd 이벤트 미등록 |
| `instructions_loaded.sh` | 미연결 | InstructionsLoaded 이벤트 미등록 |
| `skill_config_change.sh` | 미연결 | ConfigChange 이벤트 미등록 |
| `analyze_hook_log.sh` | 보조 | hook 로그 KPI 분석 (수동 실행) |

## 유틸리티 — 실행 hook 아님

| 스크립트 | 용도 |
|---|---|
| `smoke_test.sh` | 전체 hooks 구조 검증 (수동, 36/36 테스트) |

---

## 참조 파일

| 파일 | 역할 |
|---|---|
| `domain_guard_config.yaml` | 도메인별 키워드·경로·플래그 설정 (단일 기준) |
| `hook_log.txt` | stop_guard BLOCK 이력 |
