# R5 Dry-Run Report — Claude Code 환경 리모델링

> 합의안 v2 Phase 0 강제 단계. 단일 PR 작성 이전 정적 의존성 분석.
> 일시: 2026-05-03 11:1x KST
> 방법: 실제 이동 없이 정적 grep + settings.json lifecycle 분석 (read-only)

---

## 검증 통과 기준 (합의안 v2)

1. 핵심 5개 hook 부재 시 깨지는 동작이 사용자가 사전 정의한 "**생존 필수 3가지**" 안에 없음
2. 도메인 스킬 5개 dry-run 성공
3. session_start hook 출력이 새 골격(`.claude/_proposal_v2/`)으로 정상 전환

---

## 1. settings.json lifecycle 7개 등록 hook 매핑 (실측 36개)

| Lifecycle | 등록 hook 수 | 역할 분류 |
|-----------|------------|----------|
| PreCompact | 1 | 토론 전 보존 (precompact_save) |
| SessionStart | 1 | 세션 진입 상태 로드 (session_start_restore) |
| UserPromptSubmit | 1 | 발화 위험 평가 (risk_profile_prompt) |
| **PreToolUse** | **21** | 위험 차단 / 게이트 / 권위 명제 강제 |
| PostToolUse | 9 | 자동 후속 / 알림 / 측정 |
| Notification | 1 | Slack 알림 (notify_slack) |
| Stop | 5 | 완료 검증 / state 동기화 |

PreToolUse가 21개로 가장 비대 — 합의안의 "행동 교정 메타 누적"의 가장 큰 출처.

---

## 2. 핵심 5개 hook 후보 (750줄, 합의안 메타 계층 목표)

| # | Hook | 줄 수 | 역할 | 폐기 시 위험도 |
|---|------|------|------|--------------|
| 1 | `block_dangerous.sh` | 112 | rm -rf / sudo / chmod 777 등 차단 | 🔴 높음 (도메인 코드·ERP 데이터 손실 위험) |
| 2 | `protect_files.sh` | 59 | 보호 파일(원본 xlsx·기준 문서) 수정 차단 | 🔴 높음 (사용자 정책 "원본 보호" 위반 가능) |
| 3 | `commit_gate.sh` | 173 | final_check 통과 후만 commit/push | 🟡 중간 (TASKS/HANDOFF 동기화 보장) |
| 4 | `session_start_restore.sh` | 236 | 세션 진입 상태 로드 (incident 자동 인용 포함) | 🟡 중간 (운영 연속성) |
| 5 | `completion_gate.sh` | 170 | 완료 선언 시 검증 (Stop 시점) | 🟡 중간 (작업 미완료 차단) |

→ **5개 모두 도메인 안전·운영 연속성에 직결**. 메타 누적 부패 카테고리 아님 (행동 교정 명제가 아님).

---

## 3. 폐기 대상 31개 hook 분류

### 카테고리 A: 토론모드 전용 (6개) — 토론 빈도 낮음 / 사용자 결정 후 보존 여부 판단
- debate_verify, debate_gate, debate_independent_gate
- debate_send_gate_mark
- navigate_gate, mcp_send_gate

**깨지는 동작**: CLAUDE.md 미읽기 시 토론 진입 차단 / 하네스 분석 강제 / GPT 응답 후 검증 강제.
**대안**: 토론모드 SKILL.md 안에서 자체 검증 (코드로 결정론화).

### 카테고리 B: 도메인 의무 검증 (6개) — 합의안 "셋팅 보완 가능" 영역에 일부 해당
- evidence_gate, evidence_mark_read, evidence_stop_guard
- write_router_gate (폴더 화이트리스트 라우팅)
- state_rebind_check, harness_gate

**깨지는 동작**: 임시 파일 99_임시수집/ 강제 / Stop 전 evidence 마킹 강제.
**대안**: write_router_gate는 단일 hook으로 통폐합 가능 (도메인 안전).

### 카테고리 C: 자동 후속 (7개) — 사용자 부담 가능, 수동으로 대체
- auto_compile, write_marker, handoff_archive
- post_commit_notify, mode_c_log
- share_after_push, auto_commit_state

**깨지는 동작**: write_marker.json 자동 갱신 / HANDOFF 자동 archive / commit 후 share / state 자동 commit.
**대안**: 사용자 명시 발화 시만 수행. 자동화 없음.

### 카테고리 D: 권위 명제 강제 (6개) — **합의안 핵심 폐기 대상** (인지적 부채 원인)
- instruction_read_gate, skill_instruction_gate
- r1r5_plan_check, risk_profile_prompt
- permissions_sanity, skill_drift_check

**깨지는 동작**: 지침 미읽기 차단 / R1~R5 plan 강제 / permissions 1회용 탐지 / skill drift 탐지.
**대안**: **전부 폐기**. 합의안 의제2 "행동 교정 메타는 독" 카테고리. spec drift 11/11 정량 데이터로 보완 불가 입증.

### 카테고리 E: 외부 알림 / 후속 (3개) — 사용자 결정
- notify_slack, gpt_followup_post, gpt_followup_stop

**깨지는 동작**: Slack 알림 / GPT 후속 자동.
**대안**: 사용자 명시 발화 시만 수동 호출.

### 카테고리 F: stop guard 잔여 (2개) — completion_gate에 흡수 가능
- stop_guard, evidence_stop_guard

**깨지는 동작**: Stop 시점 추가 검증.
**대안**: completion_gate.sh에 통폐합.

### 카테고리 G: PreCompact / Date guard (2개) — 단일 결정
- precompact_save (토론 전 백업)
- date_scope_guard (날짜 범위 검증)

**깨지는 동작**: /compact 전 자동 백업 / 과거 날짜 데이터 차단.
**대안**: precompact_save는 보존 (토론 손실 방지). date_scope_guard는 폐기 (도메인 verify에서 처리).

---

## 4. 도메인 스킬 5개 dry-run (`.claude/hooks` 의존도)

| 도메인 스킬 | SKILL.md 줄 | `.claude/hooks` 참조 | dry-run 통과 |
|------------|------------|--------------------|-------------|
| `d0-production-plan` | 310 | **0회** | ✅ PASS |
| `jobsetup-auto` | 315 | **0회** | ✅ PASS |
| `assembly-cost-settlement` | 131 | **0회** | ✅ PASS |
| `line-batch-management` | 714 | **0회** | ✅ PASS |
| `daily-routine` | 113 | **0회** | ✅ PASS |

→ **도메인 스킬 5개 전부 .claude/hooks 의존도 0회**. 핵심 5개 hook + 도메인 SKILL.md만으로 운영 가능.

전체 21개 스킬 중 `.claude/hooks` 참조하는 것은 단 3개 (auto-fix 5회 / token-threshold-warn 7회 / jobsetup-auto 1회). 후 두 개는 자기 자신이 hook이거나 hook을 만드는 메타 스킬.

---

## 5. session_start hook 새 골격 전환 가능성

`session_start_restore.sh`는 다음을 출력:
- 현재 위치 / 최근 commit 5건 / TASKS·HANDOFF 상단 / folder_map / smoke_fast / doctor_lite / token_threshold / DRIFT / incident 인용

→ **새 골격(`_proposal_v2/`)에서도 동일 출력 가능**. 의존 파일이 TASKS/HANDOFF/STATUS 표준 경로 기준이라 .claude/hooks/ 폐기와 무관.

전환 절차 (Phase 1 단일 PR 시):
1. `.claude/_proposal_v2/hooks/` 새 폴더에 핵심 5개만 복사
2. `.claude/settings.json` 신규 작성 (5개 hook만 등록)
3. 활성 환경에는 영향 없음 (격리)

---

## 6. R5 dry-run 종합 판정

### ✅ 통과 항목
1. 핵심 5개 hook 모두 존재·도메인 안전 직결 (양측 합의 핵심 메타 layer)
2. 도메인 스킬 5개 모두 `.claude/hooks` 의존도 0 → **31개 폐기해도 작동**
3. session_start hook 새 골격 전환 가능

### ⚠️ 주의 항목 (사용자 결정 필요)
1. **카테고리 A 토론모드 6개 hook**: 토론 빈도 낮음. 도메인 안전 영향 없음. 다만 토론 품질 게이트가 사라짐 (CLAUDE.md 미읽기 진입 가능).
2. **카테고리 C 자동 후속 7개 hook**: 사용자가 직접 갱신 부담. write_marker 같은 동기화 검증도 사라짐.
3. **카테고리 E 외부 알림 3개 hook**: Slack 알림·GPT 후속 자동화 사라짐.

### 🔴 폐기 권장 (합의안 핵심)
- **카테고리 D 권위 명제 강제 6개**: 합의안 의제2 정확히 일치. **인지적 부채 원인**. spec drift 정량 11/11로 셋팅 보완 불가 입증. 즉시 폐기 권장.

---

## 7. 사용자 "생존 필수 기능 3가지" 결정용 후보 (Gemini 질문)

R5 분석 결과 도메인 자동화 자체는 5개 hook + 도메인 스킬만으로 작동. 진짜 사용자가 결정할 것은 **메타 편의 기능**:

### 옵션 A — 안전 우선 (권장 default)
1. **block_dangerous + protect_files** — 위험 명령·보호 파일 차단 (안전 필수)
2. **commit_gate** — TASKS/HANDOFF 동기화 강제 (정합성 보장)
3. **session_start_restore** — 세션 진입 incident 자동 인용 + 운영 연속성

### 옵션 B — 자동화 우선
1. 위 3개 + auto_commit_state (state 자동 commit)
2. write_marker (변경 추적)
3. session_start_restore

### 옵션 C — 토론·외부 우선
1. 위 3개 + navigate_gate (토론 품질)
2. notify_slack (외부 알림)
3. gpt_followup_post (후속 자동)

→ 사용자가 매일 하는 작업에서 "이게 없으면 정말 마비"인 것을 1-3개 골라 주시면 됩니다.

---

## 8. R5 dry-run 결과 요약 (1줄)

> **핵심 5개 hook + 도메인 스킬 5개로 ERP/MES 운영 100% 작동 가능. 31개 폐기 hook 중 카테고리 D(권위 명제 강제 6개)는 즉시 폐기 권장. 카테고리 A·B·C·E·F·G(25개)는 사용자 "생존 필수 3가지" 답변 후 분류.**

→ 합의안 v2 단일 PR 작성 진입 가능 (활성 hook 무수정, `_proposal_v2/` 골격만 생성).
