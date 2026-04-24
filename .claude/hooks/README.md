# Hooks 운영 현황

> 2026-04-20 갱신 — settings.json 등록 기준 (실제 활성 hook만 기재)
> 아카이브된 hook은 `.claude/hooks/_archive/` 참조

## 활성 Hook (32개 등록, settings.json 기준)

> **Single Source of Truth (세션93, 2026-04-22 2자 토론 합의)**: 활성 hook의 **유일한 기준축은 `list_active_hooks.sh`**. `final_check.sh`는 이 기준을 따르며, 이 문서와 `90_공통기준/업무관리/STATUS.md`의 개수 표기는 동기화 경고 용도로만 비교한다.
> - 카운트: `bash .claude/hooks/list_active_hooks.sh --count`
> - 이벤트별: `bash .claude/hooks/list_active_hooks.sh --by-event`
> - `.claude/scripts/hook_registry.sh`는 **legacy 격하** (settings.local.json 전제만 참조). 자동 sync 중단.
>
> 이벤트별 등록 수: PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 16 / PostToolUse 7 / Notification 1 / Stop 5 = **32**

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
| ⑥ | `state_rebind_check.sh` | Write\|Edit\|MultiEdit | 상태 바인딩 정합성 검사 |
| ⑦ | `mcp_send_gate.sh` | mcp__Claude_in_Chrome__form_input | Chrome MCP 토론모드 전송 전 지침 읽기 강제 (SEND GATE) |
| ⑧ | `harness_gate.sh` | Bash | 토론모드 GPT 응답 후 하네스 분석 없이 행동 차단 (채택/보류/버림 + 독립 견해 + 실물 근거 복합 조건) |
| ⑨ | `instruction_read_gate.sh` | Bash | GPT 전송 전 ENTRY.md+토론모드 CLAUDE.md 읽기 강제 |
| ⑩ | `debate_gate.sh` | mcp__Claude_in_Chrome__javascript_tool | 토론모드 활성 시 GPT 직접 JS 조작 전 지침 읽기·debate_preflight 확인 차단 |
| ⑪ | `debate_independent_gate.sh` | mcp__Claude_in_Chrome__javascript_tool | 토론모드 활성 시 독립 견해 없이 GPT 응답 전송 차단 |
| ⑫ | `navigate_gate.sh` | mcp__Claude_in_Chrome__navigate | 토론모드 활성 시 ChatGPT 직접 navigate 차단 (debate_mode 맥락 외 navigate는 통과) |
| ⑬ | `skill_instruction_gate.sh` | Bash | 인라인 python MES/ZDM 접근 시 SKILL.md 읽기 강제 |
| ⑭ | `skill_drift_check.sh` | Bash | 스킬 실행 시 최신 SKILL.md 읽기 드리프트 차단 |
| ⑮ | `debate_verify.sh` | Bash | 토론 합의 서명 검증 (`[3way]` 태그 커밋 무결성) |
| ⑯ | `permissions_sanity.sh` | Bash | settings.local.json 1회용 permissions 패턴·중복 탐지 advisory |

### 추적층 (PostToolUse)

| 훅 | matcher | 역할 |
|---|---|---|
| `auto_compile.sh` | Write\|Edit | 파일 수정 후 자동 컴파일/변환 |
| `write_marker.sh` | Write\|Edit | 파일 변경 마커 생성, 상태문서 수정 시 삭제 |
| `evidence_mark_read.sh` | Read\|Grep\|Glob\|Bash\|Write\|Edit\|MultiEdit | 문서 읽기/갱신 → .ok 증거 마커 적립 |
| `gpt_followup_post.sh` | mcp__Claude_in_Chrome\|Bash\|Edit\|Write | GPT 읽기/전송/후속작업 감지 → pending flag 관리 |
| `handoff_archive.sh` | Write\|Edit | HANDOFF.md 갱신 시 이전 세션 기록 아카이브 |
| `debate_send_gate_mark.sh` | mcp__Claude_in_Chrome__get_page_text | 토론모드 활성 시 GPT 응답 읽기 후 send_gate 마커 갱신 |
| `post_commit_notify.sh` | Bash (async) | git push 성공 시 Slack 자동 알림 발송 (event: PostToolUse) |

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
| `auto_commit_state.sh` | (전체) | 하이브리드 자동 커밋 (세션101) — 상태문서 AUTO 커밋+푸시, 나머지 리마인더 |

## 훅별 실패 책임 매트릭스 (Stop 층, 의제5 세션71 Phase 2-A 문서화)

| 훅 | 책임 영역 | 독립 가치 | 통합 시 손실 |
|---|---|---|---|
| `stop_guard.sh` | 금지 문구 기반 완료 선언 차단 (예: "미푸시 상태를 완료로") | 언어 패턴 감지 | 다른 훅이 내용 감지 안 함 |
| `gpt_followup_stop.sh` | GPT pending flag (`.claude/state/gpt_pending_*`) 존재 시 차단 | 외부 모델 대기 상태 감지 | 외부 모델 대기 중 세션 종료 |
| `completion_gate.sh` | TASKS/HANDOFF 변경 없이 "완료" 선언 차단 | 문서 동기화 강제 | 상태 원본과 세션 결론 괴리 |
| `evidence_stop_guard.sh` | req 있고 ok 없을 때 "완료/PASS" 차단 | 증거 수집 강제 | 검증 없는 완료 선언 |

결론: 각 훅 책임 직교. 통합 금지. 세션72 이후에도 유지.

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
| `mcp_send_gate.sh` | fail-open | deny JSON | debate_preflight 없으면 통과 |
| `harness_gate.sh` | fail-closed | deny JSON | transcript 미확인 시 안전 차단 |
| `instruction_read_gate.sh` | fail-closed | deny JSON | 마커 없으면 GPT 전송 차단 (decision:deny+exit 0) |
| `state_rebind_check.sh` | detect-only | 없음 | 불일치 로깅만 |
| `auto_compile.sh` | fail-open | message JSON | 컴파일 실패만 보고 |
| `write_marker.sh` | fail-open | 없음 | 마커 생성 실패해도 통과 |
| `evidence_mark_read.sh` | fail-open | 없음 | .ok 생성 실패해도 통과 |
| `gpt_followup_post.sh` | fail-open | 없음 | 플래그 생성 실패해도 통과 |
| `handoff_archive.sh` | fail-open | 없음 | 아카이브 실패해도 통과 |
| `notify_slack.sh` | fail-open | 없음 | 알림 실패해도 통과 |
| `post_commit_notify.sh` | fail-open | 없음 | push 알림 실패해도 통과 (async) |
| `stop_guard.sh` | fail-open | deny JSON | 트랜스크립트 미존재 시 통과 |
| `gpt_followup_stop.sh` | fail-open | deny JSON | 플래그 미존재 시 통과 |
| `completion_gate.sh` | fail-open | deny JSON | 마커 미존재 시 통과 |
| `evidence_stop_guard.sh` | fail-open | deny JSON | req 미존재 시 통과 |
| `debate_gate.sh` | fail-closed | deny JSON | 마커 미존재·파싱 실패 시 안전 차단 |
| `debate_independent_gate.sh` | fail-closed | deny JSON | 독립견해 마커 미존재 시 전송 차단 |
| `navigate_gate.sh` | conditional fail-closed | deny JSON | debate_mode 활성 시 fail-closed, 그 외 fail-open |
| `debate_send_gate_mark.sh` | fail-open + WARN | 없음 | 마커 생성 실패 시 WARN 로그 후 통과 (debate_gate가 2차 차단) |
| `skill_drift_check.sh` | fail-open | 없음 | advisory. SKILL.md drift 감지 시 stderr 경고만, 차단 없음 |
| `permissions_sanity.sh` | fail-open | 없음 | advisory. 1회용 패턴·완전 중복 탐지 시 stderr 경고만, 60분 캐시 |
| `auto_commit_state.sh` | fail-open (advisory) | 없음 | advisory + 자동 push. AUTO 패턴(TASKS/HANDOFF/STATUS/state) 한정. final_check.sh --fast FAIL 시 incident 기록 후 자동 commit/push 차단 (세션102 [3way]) |
| `domain_status_sync.sh` | fail-open | 없음 | advisory. 전역 TASKS 날짜 vs 도메인 STATUS.md 날짜 14일+ drift 탐지 시 stderr 경고만, 세션 차단 없음 (보조 스크립트, session_start_restore에서 호출, 세션98 C2 합의) |
| `token_threshold_check.sh` | fail-open | 없음 | advisory. 문서 비대화 임계 초과 시 stderr 경고만, exit 0 강제 (보조 스크립트, session_start_restore에서 호출) |
| `share_gate.sh` | fail-open | 없음 | advisory. 3way 감지 조건 미충족 시 stderr 경고만, 차단 없음 (보조 스크립트, share-result 수동 실행) |
| `doctor_lite.sh` | fail-open | 없음 | advisory. 설정 드리프트 감지 시 경고만, 차단 없음 (보조 스크립트) |

## req clear 규칙 (세션49 합의, 세션52 문서화)

> risk_profile_prompt.sh의 req 생명주기 규칙. 코드는 이미 구현됨, 여기는 명시적 문서화.

| 조건 | 동작 | 구현 위치 |
|------|------|----------|
| 위험 미검출 | 매 프롬프트마다 기존 `.req` 전삭제 후 키워드 매칭된 것만 재생성 | `find "$REQ_DIR" -delete` (line 23) |
| ok 존재 시 억제 | `touch_req()`에서 fresh `.ok` 파일 존재 시 req 재발행 억제 | `touch_req()` ok 신선도 검사 (line 28-38) |
| 작업단계 전환 | 매 프롬프트 재생성 구조로 흡수 — 새 프롬프트가 기존 req 자동 교체 | 전삭제+재생성 구조 자체 |

## 보조 스크립트 (settings 미등록)

| 스크립트 | 용도 |
|---|---|
| `hook_common.sh` | 공통 함수 (hook_log, safe_json_get, evidence_init, 로그 로테이션) |
| `incident_repair.py` | 최신 unresolved incident의 다음 행동 + 패치 후보 + 검증 단계 제안 |
| `smoke_test.sh` | 전체 hooks 구조 검증 (수동 실행) |
| `smoke_fast.sh` | SessionStart용 빠른 smoke (11건, 로컬/결정적만). session_start_restore.sh에서 호출 |
| `final_check.sh` | commit_gate용 자체검증 (--fast/--full). settings 미등록, commit_gate에서 호출 |
| `e2e_test.sh` | E2E 테스트 (block_dangerous/protect_files/session_start/evidence_gate 10개 시나리오). 수동 실행 |
| `doctor_lite.sh` | 경량 설정 드리프트 진단 (3자 토론 2026-04-18 합의). session_start_restore.sh에서 호출 |
| `token_threshold_check.sh` | 저장소 문서 비대화 사전 감시 (세션68 3자 합의 / 세션79 실물 구현). session_start_restore.sh에서 호출. 등급: advisory (exit 0 강제) |
| `share_gate.sh` | share-result 0단계 3way 감지 조건 자동 검증 (세션79). `/share-result` 스킬 진입 시 수동 실행. 등급: advisory (stderr 경고만) |
| `nightly_capability_check.sh` | Silent Failure 방지용 야간 capability 점검. Windows schtasks 수동 등록 필요 (세부 절차 별도 안내) |
| `pruning_observe.sh` | MEMORY/TASKS 항목 pruning 관찰 리포트 (수동 실행) |
| `list_active_hooks.sh` | 활성 hook 단일 원본 (Single Source). settings.json(team+local union) 파싱, --count/--by-event/--names/--full 모드 (세션93 SSoT 확정) |
| `../scripts/hook_registry.sh` | **[LEGACY, 세션93]** settings.local.json 전제. truth chain에서 제외. 대체: `list_active_hooks.sh` |

## 훅 등급 분류 (2026-04-19 의제5 3자 토론 합의, Phase 2-B 일부 반영)

> Phase 2-A (세션71): 등급 분류 + `hook_common.sh` 래퍼 정의.
> Phase 2-B (세션72, 2026-04-19): **핵심 훅 6종 timing 배선 + exit 2 전환 + 소프트 블록 추가**.
> Phase 2-C (세션73+): 나머지 훅 일괄 등급 주석 + incident 0건 달성 시 `debate_verify` 승격.
>
> 아래 테이블은 훅 이름을 참조용으로 나열한다. `final_check.sh`의 활성 hook 개수 기준은 상단 "활성 Hook" 섹션이며, 이 등급 분류 테이블은 별도 통계 대상이 아니다.

### Phase 2-B 적용 현황 (2026-04-19 세션72)

- **소프트 블록 신설**: `completion_gate.sh` — 1회용 3회 누적 7일 내 감지 시 deny 1회 (60초 쿨다운)
  - 세션86 관찰(2026-04-20): 발동 0건. 조건 자연 미충족(정책 gate 선제 차단으로 재발 3회 누적 미도달). **현 로직 유지**, 조건 완화·삭제 보류. 상세: `90_공통기준/업무관리/incident_audit_20260420_session86.md` §5.
- **exit 2 전환 완료 (6종)**: `commit_gate.sh`, `block_dangerous.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`(기존 유지), `stop_guard.sh`(기존 유지)
- **timing 배선만**: `debate_verify.sh` — Phase 2 승격은 incident 18건 잔존으로 보류, Phase 2-C 재평가 조건 7일 연속 0건

### 나머지 훅 등급 분류 (Phase 2-C 이월)

- **gate 승격 검토 대상**: evidence_gate / mcp_send_gate / harness_gate / instruction_read_gate / skill_instruction_gate / debate_gate / debate_independent_gate / navigate_gate / gpt_followup_stop
- **advisory 유지**: state_rebind_check / permissions_sanity / auto_compile / skill_drift_check
- **measurement (timing 배선 예정)**: write_marker / handoff_archive / evidence_mark_read / debate_send_gate_mark / gpt_followup_post / post_commit_notify / notify_slack / session_start_restore / precompact_save / risk_profile_prompt

### 공통 래퍼 사용 예 (Phase 2-C 이관 시 참고)
```bash
source "$(dirname "$0")/hook_common.sh"

# advisory 훅 호출 (실패해도 계속):
hook_advisory "permissions_sanity" bash .claude/hooks/permissions_sanity.sh

# gate 훅 호출 (실패 시 exit 2):
hook_gate "commit_gate" bash .claude/hooks/commit_gate.sh

# measurement 훅 호출 (영향 없음):
hook_measure "handoff_archive" bash .claude/hooks/handoff_archive.sh
```

### 통합·순서 평가 (의제4 세션72 이월)
- `hook_timing.jsonl` 수집 (advisory·measurement 성격 훅 대상, Phase 2-A 신설)
- 1주일 누적 후 의제4에서 통합 후보 평가
- 고정 순서: `block_dangerous` → `commit_gate` → `debate_verify` (절대 변경 금지)

## 참조

| 파일 | 역할 |
|---|---|
| `hook_log.jsonl` | hook 실행 이력 JSONL (500KB 로테이션) |
| `_archive/` | 비활성화된 hook 보관 (send_gate.sh 포함) |
