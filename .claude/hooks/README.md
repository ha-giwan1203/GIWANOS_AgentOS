# Hooks 운영 현황

> 2026-04-11 갱신 — settings.local.json 등록 기준 (실제 활성 hook만 기재)
> 아카이브된 hook은 `.claude/hooks/_archive/` 참조

## 활성 Hook (20개 스크립트, settings.local.json 등록)

> `final_check.sh`는 `settings.local.json`의 실제 등록 목록을 기준축으로 보고, 이 문서와 `90_공통기준/업무관리/STATUS.md`의 개수 표기는 동기화 경고 용도로만 비교한다.

### 이벤트층 (SessionStart / PreCompact)

| 훅 | matcher | 역할 |
|---|---|---|
| `session_start_restore.sh` | SessionStart | 세션 시작 시 이전 상태 복원 (compact 저장 → 복원) |
| `precompact_save.sh` | PreCompact | 컨텍스트 압축 직전 핵심 상태 저장 |

### 프롬프트층 (UserPromptSubmit)

| 훅 | matcher | 역할 |
|---|---|---|
| `risk_profile_prompt.sh` | (전체) | 프롬프트 위험 키워드 감지 → .req 파일 생성 |

### 차단층 (PreToolUse)

> **등록 순서**: settings.local.json 배열 순서대로 등록. 각 훅은 독립 실행되며 하나가 deny해도 다른 훅 실행 여부는 Claude Code 내부 구현에 의존.
> Bash 매처 3개(①②③)는 각각 독립적으로 차단 판정. 설계 의도상 파괴 차단 → 커밋 게이트 → 날짜 범위 순.

| 순서 | 훅 | matcher | 역할 |
|---|---|---|---|
| ① | `block_dangerous.sh` | Bash | 극단 파괴 명령 + 보호 경로 삭제/이동 차단 |
| ② | `commit_gate.sh` | Bash | git commit/push 전 final_check 강제 (--fast/--full 자동 판정) |
| ③ | `date_scope_guard.sh` | Bash | ZDM/일상점검 일요일·일괄범위·MM/DD 차단 |
| ④ | `evidence_gate.sh` | Bash\|Write\|Edit\|MultiEdit | req있고 ok없으면 위험 실행 deny |
| ⑤ | `protect_files.sh` | Write\|Edit\|MultiEdit | 원본 엑셀/아카이브/기준정보 수정 차단 |
| ⑥ | `send_gate.sh` | mcp__Claude_in_Chrome__javascript_tool | 토론모드 전송 전 미확인 응답 점검, `tool_input` 우선 파싱 |
| ⑦ | `state_rebind_check.sh` | Bash | 상태 바인딩 정합성 검사 |

### 추적층 (PostToolUse)

| 훅 | matcher | 역할 |
|---|---|---|
| `auto_compile.sh` | Write\|Edit | 파일 수정 후 자동 컴파일/변환 |
| `write_marker.sh` | Write\|Edit | 파일 변경 마커 생성, 상태문서 수정 시 삭제 |
| `evidence_mark_read.sh` | Read\|Grep\|Glob\|Bash\|Write\|Edit\|MultiEdit | 문서 읽기/갱신 → .ok 증거 마커 적립 |
| `gpt_followup_post.sh` | mcp__Claude_in_Chrome\|Bash\|Edit\|Write | GPT 읽기/전송/후속작업 감지 → pending flag 관리 |
| `handoff_archive.sh` | Write\|Edit | HANDOFF.md 갱신 시 이전 세션 기록 아카이브 |

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
| `evidence_stop_guard.sh` | (전체) | 증거 없는 실패/완료 결론 차단 |

## 훅별 실패 계약 (Failure Contract)

> 각 훅이 내부 오류(파싱 실패, 파일 미존재 등)를 만났을 때의 동작 정책.
> **fail-open**: 오류 시 통과 (exit 0). **fail-closed**: 오류 시 차단 (deny/block).
> **detect-only**: 로그만 남기고 통과.

| 훅 | 정책 | stdout intent | 비고 |
|---|---|---|---|
| `session_start_restore.sh` | fail-open | 없음 | 복원 실패해도 세션 시작 차단 안 함 |
| `precompact_save.sh` | fail-open | 없음 | 저장 실패해도 compact 진행 |
| `risk_profile_prompt.sh` | fail-open | 없음 | .req 생성 실패 시 gate 비활성화 |
| `block_dangerous.sh` | fail-closed | deny JSON | 파싱 실패 시 안전 차단 |
| `commit_gate.sh` | fail-open (hardened) | deny JSON | 파싱 실패 시 raw INPUT fallback 검사 후 통과 |
| `date_scope_guard.sh` | fail-open | deny JSON | 날짜 파싱 실패 시 통과 |
| `evidence_gate.sh` | fail-open | deny JSON | req 없으면 전체 통과 |
| `protect_files.sh` | fail-open | deny JSON | 파싱 실패 시 통과 |
| `send_gate.sh` | fail-open | deny JSON | 파싱 실패 시 전송 허용 |
| `state_rebind_check.sh` | detect-only | 없음 | 불일치 로깅만 |
| `auto_compile.sh` | fail-open | message JSON | 컴파일 실패만 보고 |
| `write_marker.sh` | fail-open | 없음 | 마커 생성 실패해도 통과 |
| `evidence_mark_read.sh` | fail-open | 없음 | .ok 생성 실패해도 통과 |
| `gpt_followup_post.sh` | fail-open | 없음 | 플래그 생성 실패해도 통과 |
| `handoff_archive.sh` | fail-open | 없음 | 아카이브 실패해도 통과 |
| `notify_slack.sh` | fail-open | 없음 | 알림 실패해도 통과 |
| `stop_guard.sh` | fail-open | block JSON | 트랜스크립트 미존재 시 통과 |
| `gpt_followup_stop.sh` | fail-open | block JSON | 플래그 미존재 시 통과 |
| `completion_gate.sh` | fail-open | block JSON | 마커 미존재 시 통과 |
| `evidence_stop_guard.sh` | fail-open | block JSON | req 미존재 시 통과 |

## 보조 스크립트 (settings 미등록)

| 스크립트 | 용도 |
|---|---|
| `hook_common.sh` | 공통 함수 (hook_log, safe_json_get, evidence_init, 로그 로테이션) |
| `incident_repair.py` | 최신 unresolved incident의 다음 행동 + 패치 후보 + 검증 단계 제안 |
| `smoke_test.sh` | 전체 hooks 구조 검증 (수동 실행) |
| `final_check.sh` | commit_gate용 자체검증 (--fast/--full). settings 미등록, commit_gate에서 호출 |

## 참조

| 파일 | 역할 |
|---|---|
| `hook_log.jsonl` | hook 실행 이력 JSONL (500KB 로테이션) |
| `_archive/` | 비활성화된 hook 20개 보관 |
