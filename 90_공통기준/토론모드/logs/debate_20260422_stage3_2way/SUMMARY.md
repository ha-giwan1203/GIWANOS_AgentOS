# 단계 III 2자 토론 SUMMARY

**세션**: 91 (2026-04-22)
**모드**: 2자 토론 (Claude × GPT gpt-5-4-thinking)
**의제**: Plan glimmering-churning-reef 단계 III — 게이트 3종 범위 재절단 (원칙 5 "1 Problem ↔ 1 Hook")
**라운드**: 4 (Round 1 의제 제시 → Round 2 합의 확정 → Round 3 조건 수용 + 종결 → Round 4 critic WARN 재판정)
**최종 판정**: GPT 통과 (critic WARN 실측 재검증으로 해소)

---

## 합의 결과 (5의제 + 조건 1건)

| 의제 | 판정 | 합의 내용 |
|------|------|----------|
| 1. commit_gate write_marker 동봉 로직 이전 방향 | 채택 (B 삭제) | commit_gate.sh L81-98 삭제. write_marker는 그대로 남겨 completion_gate에서만 소비. A안(이관)의 풋건: Stop 훅에 `git log -1 --name-only HEAD` 섞으면 다중 커밋 세션에서 HEAD 기준 드리프트 |
| 2. evidence_gate 300s suppress가 "사전 근거" 위반? | 채택 (미위반) | 300s는 incident 기록 억제일 뿐 permissionDecision 완화 아님. 라벨은 `suppress_reason=evidence_recent`를 hook_log/stderr에 고정 (incident_ledger row 생성 금지 — suppress 의미 파괴 방지) |
| 3. III-4 gate_boundary_check grep 오탐 | 채택 (대안 2) | grep tripwire + `# [gate-boundary-allow]` 화이트리스트. 단, full-line comment/blank 제외 후 검사. 성격: "회귀 트립와이어" (정합성 증명 아님) |
| 4. III-5 동반 3개 실제 수정 필요 여부 | 채택 (수정 포함, Round 4 사유 교체) | write_marker 무수정 (소비자 이관 없음) / evidence_mark_read 무수정 / **evidence_stop_guard.sh L63-70 (3번 블록) 제거** — 사유: **tasks_handoff req producer 제거 이후 남은 latent completion branch 정리 + completion 책임 단일화** (실측 grep 0 matches 근거). 1번(auth_diag)·2번(skill_read/identifier) 블록은 evidence 본연 역할 유지 |
| 5. 커밋 단위 | 채택 (4커밋, Claude 초안 수정) | A: commit_gate 축소 / B: evidence_stop_guard 완료축 제거 / C: evidence_gate suppress 라벨 / D: gate_boundary_check 신설 + smoke_fast 편입 |
| 조건 1건 (Round 2 GPT) | 채택 | D 커밋에서 **standalone 실행 1회 → 오탐 확인 + 화이트리스트 반영 → smoke_fast 편입** 순 고정 |

---

## 의존 관계 최종

- 의제 1 → 의제 5: B 채택으로 "이관 커밋" 삭제 → 커밋 A/B 구조 확정
- 의제 4 → 의제 5: evidence_stop_guard 3번 블록 제거가 커밋 B에 포함
- 의제 3 → 의제 5: boundary_check는 반드시 마지막 (커밋 D). 먼저 넣으면 초반 커밋 오탐 가능

---

## 단계 III 최종 실행 계획 (구현 세션92 이후)

### 커밋 A: commit_gate.sh L81-98 제거
- `.claude/hooks/commit_gate.sh` L81-98 (write_marker 존재 시 TASKS/HANDOFF staged 검증 블록) 삭제
- 커밋 직후 smoke_fast 10/10 PASS 확인
- write_marker.sh / completion_gate.sh 무수정

### 커밋 B: evidence_stop_guard.sh L63-70 제거
- 사유: **tasks_handoff req producer 제거 이후 남은 latent completion branch 정리 + completion 책임 단일화** (Round 4 문구 수정)
  - 실측: `risk_profile_prompt.sh` L66-69 세션78 P2 재정의 주석이 tasks_handoff 조기 트리거 완전 제거 명시
  - 저장소 전역 grep `touch_req.*tasks_handoff` 0 matches → producer 없음
  - 따라서 L63-70의 `fresh_req "tasks_handoff"` 조건은 dead branch
- `.claude/hooks/evidence_stop_guard.sh` L63-70 (tasks_handoff.req + 완료/PASS 차단 블록) 삭제
- 1번(auth_diag) · 2번(skill_read/identifier) 블록은 유지
- 커밋 직후 smoke_fast 10/10 PASS 확인

### 커밋 C: evidence_gate.sh suppress 라벨 고정
- `.claude/hooks/evidence_gate.sh` suppress 경로의 hook_log/stderr 출력에 `suppress_reason=evidence_recent` 문자열 명시
- incident_ledger row 생성 금지
- 커밋 직후 smoke_fast 10/10 PASS 확인

### 커밋 D: gate_boundary_check.sh 신설 + smoke_fast 편입
- **단계 1 (standalone)**: `.claude/hooks/gate_boundary_check.sh` 신설
  - full-line comment (`^\s*#`) + blank line 제외 후 grep
  - `# [gate-boundary-allow]` 주석 화이트리스트 (해당 라인만 예외)
  - 검사 대상:
    - commit_gate.sh에 TASKS/HANDOFF/STATUS 경로 → 발견 시 FAIL
    - evidence_gate.sh에 Git diff/staged → 발견 시 FAIL
    - completion_gate.sh에 evidence·근거 수집 → 발견 시 FAIL
  - `bash .claude/hooks/gate_boundary_check.sh` 단독 실행 1회 → 결과 기록
- **단계 2**: 단독 실행 결과 검토 → 오탐 확인 → 필요 시 `# [gate-boundary-allow]` 주석 반영
- **단계 3**: smoke_fast.sh에 편입 (각 게이트 수정 커밋 시 자동 실행)
- 커밋 직후 smoke_fast 10/10 PASS 확인

---

## 계획 파일 갱신 범위

**C:/Users/User/.claude/plans/glimmering-churning-reef.md Part 3 단계 III**:
- III-1: "commit_gate.sh L81-98 write_marker 동봉 강제 삭제"로 구체화 (선택지 B 채택)
- III-2: "evidence_gate.sh suppress 라벨 hook_log/stderr 고정 (`suppress_reason=evidence_recent`)"로 구체화
- III-3: "completion_gate.sh 현 상태 유지"로 변경 (책임 이관 없음)
- III-4: "gate_boundary_check.sh 신설 — standalone 1회 → 오탐 확인 → smoke_fast 편입 순" 고정
- III-5: "evidence_stop_guard.sh L63-70 (3번 블록) 제거" 항목 신설. write_marker / evidence_mark_read 무수정 명시
- 커밋 단위를 A/B/C/D 4건으로 확정 (세션별 1커밋 1논리단위 유지)

---

## 회귀 테스트 베이스라인 (2026-04-22 11:01 KST)

- smoke_fast: 10/10 ALL PASS
- settings.json 활성 hook 수: 31개 ↔ README.md 31개 동기
- settings_drift invariant: WAIVER 적용 중 (V-1/V-2 후 복원)

---

## 구현 착수 조건

- 본 세션91은 토론 종결까지만.
- 구현은 **세션92 이후**에서 착수. 조건:
  - B4 Circuit Breaker 일일 T2 구조변경 상한(2건) 준수
  - NEW_HOOK_CHECKLIST 증적 번들 강제 (gate_boundary_check 신설 시 실측 데이터 / 의존 그래프 / 예산 4종 / TTL 30일 / 제거 조건 명시)
  - 1커밋 1논리단위 준수
  - 각 커밋 직후 smoke_fast 10/10 PASS 확인, 실패 시 즉시 revert

---

## 종결 서명

- Claude: 하네스 분석 완료, 5의제 + 조건 1건 전부 채택. Round 4에서 critic WARN 실측 재검증 수행 (grep 0 matches + risk_profile_prompt.sh L66-69 producer 제거 주석 실증)
- GPT: 통과 (gpt-5-4-thinking, Round 3) + Round 4 critic 지적 기각 + SUMMARY 문구 교체 합의
- 본 토론은 설계 합의. 실제 파일 수정은 별도 세션에서 commit-by-commit 수행.

## critic-reviewer 감사 기록

- Step 4b critic-reviewer 판정: **WARN** (4축 중 독립성 WARN / 하네스 FAIL / 0건감사 WARN / 일방성 WARN)
- 핵심 지적: 의제 4 "완료축 중복" 주장이 실측 없이 "실증됨" 통과
- 해소 경로: Round 4에서 GPT에 실측 근거 요청 → GPT가 risk_profile_prompt.sh producer 제거 명시 + grep 0 matches 근거 제시 → Claude 독립 재검증 → 실증 확인 → "보완 관계"가 아닌 "dead branch"로 판정 고정
- 결론: 커밋 B 유지. 단 사유 문구는 "중복" → "latent completion branch 정리 + completion 책임 단일화"로 교체
