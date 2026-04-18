# 의제5 — hook vs permissions 중복 감사 리포트

> **목적**: 3자 토론(의제5) 입력용 read-only 감사. 현재 시스템의 hook 목록·permissions.allow 항목·중복/충돌/1회용 흔적을 정리하여 토론 시 독립 근거로 사용.
> **작성**: 2026-04-18 세션70 Claude (read-only, 로직 변경 없음)
> **기준 파일**: `.claude/settings.local.json`, `.claude/hooks/*.sh|*.py`

---

## 1. Hook 실물 목록 (총 35개 .sh + 5개 .py)

### 1-1. 이벤트별 hook 배치

| 이벤트 | 그룹 수 | 매처·hook |
|--------|--------|----------|
| SessionStart | 1 | (global) session_start_restore |
| PreCompact | 1 | (global) precompact_save |
| UserPromptSubmit | 1 | (global) risk_profile_prompt |
| PreToolUse | 14 | ↓ 아래 상세 |
| PostToolUse | 7 | ↓ 아래 상세 |
| Notification | 1 | (global) notify_slack |
| Stop | 4 | (global) stop_guard → gpt_followup_stop → completion_gate → evidence_stop_guard |

### 1-2. PreToolUse Bash 매처 실행 순서 (7개 순차)

1. `block_dangerous` — 위험 명령 차단
2. `commit_gate` — 커밋 전 기준 문서 갱신·incident 체크
3. `debate_verify` — 3way 커밋 시 서명 검증 (Phase 1 경고)
4. `date_scope_guard` — 날짜 스코프 guard
5. `harness_gate` — 하네스 분석 누락 차단
6. `instruction_read_gate` — 지시문 미읽기 차단
7. `skill_instruction_gate` — 스킬 사용 강제

### 1-3. PreToolUse Write|Edit|MultiEdit 매처

- `evidence_gate` (Bash도 포함)
- `protect_files`
- `state_rebind_check`

### 1-4. PreToolUse MCP 매처

- `mcp_send_gate` — form_input
- `debate_gate` — javascript_tool
- `debate_independent_gate` — javascript_tool
- `navigate_gate` — navigate

### 1-5. PostToolUse 매처

- `auto_compile` [Write|Edit]
- `write_marker` [Write|Edit]
- `handoff_archive` [Write|Edit]
- `evidence_mark_read` [Read|Grep|Glob|Bash|Write|Edit|MultiEdit] — **거의 모든 도구 후 실행**
- `debate_send_gate_mark` [get_page_text]
- `gpt_followup_post` [mcp__Claude_in_Chrome|Bash|Edit|Write]
- `post_commit_notify` [Bash, async]

---

## 2. permissions.allow 실물 (총 109 항목)

### 2-1. 완전 동일 중복 (2건)

| 항목 | 등록 횟수 |
|------|----------|
| `Bash(cat:*)` | x2 |
| `Bash(echo:*)` | x2 |

**원인**: 세션69 추가 시 기존 항목을 확인하지 않고 포괄 패턴 재등록 (구체 경로 버전 + 포괄 버전 병존)

### 2-2. 1회용 의심 항목 (16건)

| 분류 | 예시 |
|------|------|
| 특정 PID echo (8건) | `Bash(echo "1382935380")`, `Bash(echo "1382937453")` 등 — 탭 ID 하드코딩 |
| 특정 URL echo (3건) | `Bash(echo "https://chatgpt.com/c/69ddbd0e-...")` 등 — 대화방 URL 하드코딩 |
| 특정 파일 rm (1건) | `Bash(rm -f "C:/.../네임플레이트_양식정리.xlsx")` |
| 특정 디렉토리 rmdir (1건) | `Bash(rmdir "C:/.../공정 매트릭스")` |
| state 파일 rm (2건) | `Bash(rm -f .claude/state/active_domain.req)` 등 |
| 1회성 sed (1건) | `Bash(sed -i 's/^최종 업데이트: 2026-04-18 — 세션64.*/... 테스트용 강제 드리프트.../' ...)` — 드리프트 테스트 흔적 |

### 2-3. dedicated tool 중첩 (10건)

Claude Code 기본 가이드는 Grep/Glob/Read 등 전용 도구 우선. `Bash(xxx:*)` 허용은 fallback 용도지만 일부는 중복:

| 항목 | 비고 |
|------|------|
| `Bash(ls:*)` | Glob 대체 가능 (디렉토리 탐색) |
| `Bash(wc:*)` | 라인 수 등 지표 |
| `Bash(find:*)` | Glob 대체 |
| `Bash(grep:*)` | Grep 대체 |
| `Bash(cat:*)` x2 | Read 대체 |
| `Bash(head:*)` | Read(offset/limit) 대체 |
| `Bash(tail:*)` | Read(offset/limit) 대체 |
| `Bash(echo:*)` x2 | 출력 불필요 (assistant text로 대체) |

### 2-4. 구체 경로 Bash 허용 (대표)

- `Bash(python3 "90_공통기준/업무관리/운영검증/scripts/*":*)`
- `Bash(PYTHONUTF8=1 python "90_공통기준/스킬/youtube-analysis/*":*)`
- `Bash(python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py")`
- `Bash(python3 \"C:/Users/User/Desktop/업무리스트/.claude/hooks/incident_review.py\" --days 7 --threshold 3)`

**쟁점**: 포괄 `Bash(python3:*)` 허용이 있으면 이 구체 경로들은 불필요. 현재 `Bash(python3)` 단독 허용은 있으나 `Bash(python3:*)`는 없고 `Bash(python*:*)`는 `ask` 목록.

---

## 3. Hook vs permissions 기능 중첩 가능성

| 영역 | hook 보장 | permissions 보장 | 중첩 여부 |
|------|----------|-----------------|----------|
| 위험 명령 차단 | `block_dangerous.sh` | `permissions.ask` (일부) | 부분 중첩 — hook이 더 광범위. ask는 `python*`·`cp`·`mv`·`chmod`·`cmd /c`·`powershell`·`taskkill` 7개만 |
| 커밋 품질 | `commit_gate.sh` | 없음 | hook 전용 |
| 3way 서명 | `debate_verify.sh` | 없음 | hook 전용 |
| Chrome 조작 gate | `navigate_gate.sh`, `debate_gate.sh`, `debate_independent_gate.sh`, `mcp_send_gate.sh` | `mcp__Claude_in_Chrome__*` 허용 (4개 개별) | **기능 직교** — permissions는 도구 호출 허용/불허, hook은 맥락 검증 |
| 지시문 읽기 강제 | `instruction_read_gate.sh` + `skill_instruction_gate.sh` | 없음 | hook 전용 |
| 증거 수집 | `evidence_gate.sh` + `evidence_mark_read.sh` + `evidence_stop_guard.sh` | 없음 | hook 전용 (3개 연계) |

**기능 직교 판정**: permissions.allow는 "이 도구 호출 자체를 허용할지", hook은 "호출 시점에 맥락이 맞는지". 대부분 중첩 아닌 직교. 다만 1회용 permissions 항목은 실질적 보안 가치 없음.

---

## 4. 주요 쟁점 후보 (토론 입력용)

### 쟁점 A — 1회용 permissions 항목 정리
- 16건 제거 후보. echo PID/URL은 차기 세션에서 즉시 재등장 (세션마다 탭 ID 변경) → 영구 무의미
- 제거 시 리스크: 새 PID echo 요청 팝업 재발생 → 사용자 클릭 비용 증가
- 대안: `Bash(echo:*)` 포괄 허용으로 흡수 (이미 등록됨 x2)

### 쟁점 B — 완전 동일 중복 제거
- `Bash(cat:*)` x2, `Bash(echo:*)` x2 — 중복 등록만 제거하면 됨 (무손실)

### 쟁점 C — dedicated tool 중첩 Bash 허용 유지 여부
- `ls/wc/find/grep/cat/head/tail/echo` 10건 — Claude가 Bash로 이들을 호출하지 못하면 Grep/Glob/Read만 사용
- 실제로 assistant가 `Bash(cat ...)` 호출하는 경우 있음 (JSON 파싱 전 구조 확인 등) → 제거 시 작업 지연
- 유지 권장 (실무 편의 > 보안 이득)

### 쟁점 D — PreToolUse Bash 매처 7개 순차 실행 비용
- 모든 Bash 호출마다 7개 hook 실행. 매 호출 수백 ms 오버헤드 가능
- 병렬화·통합 고려 가능하나 순서 의존성 존재 (block_dangerous는 가장 먼저, debate_verify는 commit_gate 뒤)
- → **의제4 `/debate-verify` 실행 순서 재평가**와 연계

### 쟁점 E — Stop hook 4개 순차 실행
- stop_guard / gpt_followup_stop / completion_gate / evidence_stop_guard
- 세션 종료 시마다 4회 hook 실행. 각 책임 분리 명확 (유지 타당)

### 쟁점 F — hook vs permissions 역할 경계 명문화
- 현재 묵시적으로 "permissions = 도구 호출 허용, hook = 맥락 검증"
- 문서화 부재. 신규 hook 또는 permissions 추가 시 혼란 가능 → 명문화 필요성

---

## 5. 수치 요약

- 총 hook 파일: 35 `.sh` + 5 `.py`
- 총 hook 실행 지점(매처-커맨드 쌍): 29개 (PreCompact 1 + SessionStart 1 + UserPromptSubmit 1 + PreToolUse 14 + PostToolUse 7 + Notification 1 + Stop 4)
- 총 permissions.allow: 109 항목
- 정리 후보: 최대 18건 (1회용 16 + 완전 중복 2)
- dedicated 중첩(판단 보류): 10건

---

## 6. 출력 데이터 (토론 시 재계산 없이 참조용)

- Bash 매처 PreToolUse 실행 순서 7개
- PostToolUse `evidence_mark_read` 매처 범위: `Read|Grep|Glob|Bash|Write|Edit|MultiEdit`
- Stop hook 4개 순서
- permissions.ask 7개 항목(`python*`, `pip`, `cp`, `mv`, `chmod`, `cmd /c`, `powershell`, `taskkill`)
