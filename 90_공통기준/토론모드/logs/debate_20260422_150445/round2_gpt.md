# Round 2 — GPT 응답 (실행계획 문서)

## 보류 해소 1 — evidence 3종 = evidence-core만

### A. evidence-core로 남길 마커 (week1+week2 경로)
- `date_check.ok` — evidence_gate, evidence_stop_guard 사용
- `auth_diag.ok` — evidence_gate, evidence_stop_guard 사용
- `identifier_ref.ok` — evidence_gate, evidence_stop_guard 사용

### B. instruction/control 축으로 분리 유지할 마커
- `debate_entry_read.ok`, `debate_claude_read.ok` — mcp_send_gate, instruction_read_gate
- `domain_<domain>__<doc>.ok` — instruction_read_gate 동적
- `skill_read__<skill>.ok` — skill_instruction_gate (evidence_gate 보조 면제 조건은 week1 제거)
- `debate_send_gate.ok` — debate_gate
- `debate_independent_review.ok` — debate_independent_gate

### C. 직접 의존 못 찾은 마커 (week2 "보존 이유 없으면 삭제" 후보)
- `skill_read.ok`, `domain_read`, `tasks_read`, `handoff_read`, `status_read`

## 보류 해소 2 — boundary 시나리오 카탈로그 (smoke_test 신규 runtime 케이스)

### 축 1: commit_gate ↔ completion_gate
1. `git push 단독` — 기대: commit_gate skip_push_only / completion_gate 무관. push-only skip 회귀 방지
2. `강한 완료 주장 + git dirty` — 기대: completion_gate deny(completion_before_git) / commit_gate 비개입. 완료 검증 책임이 commit이 아닌 completion임을 runtime 보증

### 축 2: evidence_gate ↔ commit_gate
3. `git commit + evidence req 없음` — 기대: week1 이후 evidence_gate 통과, commit_gate/final_check만 판정. commit 책임이 evidence로 새지 않음을 보증

### 축 3: completion_gate ↔ evidence_stop_guard
4. `로그인 실패 결론 + auth_diag.req 미해결` — 기대: evidence_stop_guard block, completion_gate skip_noclaim
5. `완료 보고 + auth/date/id req 없음` — 기대: completion_gate 판정, evidence_stop_guard 비개입

## 1주차 작업묶음

### 1. drift source 정리 (hook_registry 격하)
- 파일: `.claude/scripts/hook_registry.sh` / `.claude/hooks/list_active_hooks.sh` / `.claude/hooks/final_check.sh` / `.claude/hooks/README.md` / `90_공통기준/업무관리/STATUS.md`
- 변경 요지: hook_registry.sh를 truth chain에서 제외, list_active_hooks + final_check를 단일 기준으로 고정, hook_registry 폐기 또는 legacy/local-only 격하. README/STATUS 문구 통일
- 예상 소요: 30분~1시간
- 선행: 없음

### 2. selfcheck 24h 정확 집계
- 파일: `.claude/self/selfcheck.sh`
- 변경 요지: prefix grep 제거. 정확한 timestamp 비교로 교체
- 선행: 없음

### 3. doctor_lite fallback
- 파일: `.claude/hooks/doctor_lite.sh`
- 변경 요지: python/python3 fallback (smoke_fast와 동일 패턴)
- 선행: 없음

### 4. evidence coverage 축소
- 파일: `.claude/hooks/risk_profile_prompt.sh` / `evidence_gate.sh` / `evidence_stop_guard.sh` / `evidence_mark_read.sh` / `smoke_test.sh`
- 변경 요지: evidence-core 3종만 남김. tasks_handoff commit 경로 제거(commit_gate/final_check + completion_gate로 이관). map_scope / map_scope_warn / generic skill_read.req 제거. skill_read__X, debate_*, domain_*는 instruction/control 축 유지. **이 단계는 coverage만 축소, 3종 contract 완성은 2주차**
- 예상 소요: 반나절~1일
- 선행: 2번, 3번

## 1주차 검증 기준
- hook_registry 비활성: `list_active_hooks --count`와 `final_check` 기준 숫자 일치
- selfcheck 24h = 독립 one-liner 계산과 일치
- doctor_lite python/python3 fallback (smoke_fast와 동일 환경 탄력성)
- evidence coverage 축소 후 1주 관찰: `evidence_gate` 7일 미해결 건수 감소 추세 확인

## 2주차 작업묶음

### 5. evidence 3종 contract형 재설계
- 파일: `risk_profile_prompt.sh` / `evidence_gate.sh` / `evidence_mark_read.sh` / `evidence_stop_guard.sh` + README
- 변경 요지: date/auth/identifier 3종을 키워드+grep+suppression이 아닌 **provider-contract**로 전환. "무슨 텍스트를 읽었나" → "어떤 검증 행위를 했고 결과가 무엇인가". Claude 의견 (라) 채택: evidence만의 문제가 아니라 selfcheck/gate_boundary 포함 "grep 기반 근사 → 이벤트 기반 계약" 전환의 시작점. 다만 **순서는 evidence 먼저** (노이즈 축소 후 contract 설계가 단순)
- 예상 소요: 1~2일
- 선행: 1주차 4번 완료 + 1주 관찰 데이터

### 6. 상태 복원 축 경량화
- 파일: `precompact_save.sh` / `session_start_restore.sh` / `state_rebind_check.sh` + README
- 변경 요지: state_rebind_check를 content injection → detect-only 경고. precompact_save의 kernel/progress/task_cursor 저장 얇게. 복원은 session_start_restore 한 곳만. SessionStart fallback 유지, 쓰기 직전 TASKS/HANDOFF 재주입 중단
- 예상 소요: 반나절~1일
- 선행: 5번 권장 (최소 4번 완료)

### 7. boundary smoke 시나리오 승격
- 파일: `smoke_test.sh` / `smoke_fast.sh` / `gate_boundary_check.sh` + 필요 시 test fixture `.claude/hooks/testdata/` 또는 `_fixtures/`
- 변경 요지: gate_boundary_check는 lint/냄새 탐지기 유지. 실제 보증은 week1 정의 boundary 시나리오 6개를 smoke_test runtime 케이스로 추가. smoke_fast에는 1건만(commit responsibility no longer lives in evidence). Stop-hook transcript 기반 테스트는 fixture 추가
- 예상 소요: 반나절~1일
- 선행: 5번, 6번

## 2주차 검증 기준
(GPT 답변 중 명시적으로 열거되진 않았으나 롤백 조건 항목에 통합됨)

## 롤백 조건 (단계별)
- **hook_registry 제거** 후 `final_check` 숫자 불일치 → legacy 격하 복귀
- **evidence coverage 축소** 후 incident 오히려 증가 → 해당 req만 선택적 복구
- **contract 전환** 후 false-negative 발생 → shorter excerpt로 복귀
- **boundary smoke 승격** 후 신규 케이스 flaky → 해당 케이스만 fixture 보강 전까지 제외, gate_boundary_check lint 유지

## 손대지 않기로 한 축 재확인 리스트
- `block_dangerous.sh` fail-closed 파괴 명령 차단
- `commit_gate.sh` final_check 소유권, push-only skip
- `completion_gate.sh` 강한 완료 주장 + git/state sync
- `write_marker.json` / `after_state_sync` 계약
- `SessionStart fallback` (kernel stale/missing 시 TASKS/HANDOFF 원문 fallback)
- 토론/스킬 instruction/control 마커 계열 (debate_entry_read, debate_claude_read, skill_read__, domain_*__*, debate_send_gate, debate_independent_review)
- fingerprint 키 정의 (week1에는 안 건드림)
