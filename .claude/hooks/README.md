# Hooks 운영 현황

> 2026-04-06 갱신 — settings.local.json 등록 기준 (실제 활성 hook만 기재)
> 아카이브된 hook은 `.claude/hooks/_archive/` 참조

## 활성 Hook (10개 스크립트, settings.local.json 등록)

### 차단층 (PreToolUse)

| 훅 | matcher | 역할 |
|---|---|---|
| `block_dangerous.sh` | Bash | 극단 파괴 명령 + 보호 경로 삭제/이동 차단 |
| `protect_files.sh` | Write\|Edit\|MultiEdit | 원본 엑셀/아카이브/기준정보 수정 차단 |
| `send_gate.sh` | mcp__Claude_in_Chrome__javascript_tool | 토론모드 전송 전 미확인 응답 점검 |

### 추적층 (PostToolUse)

| 훅 | matcher | 역할 |
|---|---|---|
| `auto_compile.sh` | Write\|Edit | 파일 수정 후 자동 컴파일/변환 |
| `write_marker.sh` | Write\|Edit | 파일 변경 마커 생성, 상태문서 수정 시 삭제 |
| `gpt_followup_post.sh` | mcp__Claude_in_Chrome\|Bash\|Edit\|Write | GPT 읽기/전송/후속작업 감지 → pending flag 관리 |

### 알림층 (Notification)

| 훅 | matcher | 역할 |
|---|---|---|
| `notify_slack.sh` | (전체, async) | Slack 채널 알림 발송 |

### 종료층 (Stop)

| 훅 | matcher | 역할 |
|---|---|---|
| `stop_guard.sh` | (전체) | 금지 문구 포함 시 Stop 차단 |
| `gpt_followup_stop.sh` | (전체) | GPT pending flag 존재 시 Stop 차단 |
| `completion_gate.sh` | (전체) | TASKS/HANDOFF 미갱신 시 Stop 차단 |

## 보조 스크립트 (settings 미등록)

| 스크립트 | 용도 |
|---|---|
| `hook_common.sh` | 공통 함수 (hook_log, 로그 로테이션) |
| `smoke_test.sh` | 전체 hooks 구조 검증 (수동 실행) |

## 참조

| 파일 | 역할 |
|---|---|
| `hook_log.jsonl` | hook 실행 이력 JSONL (500KB 로테이션) |
| `_archive/` | 비활성화된 hook 20개 보관 |
