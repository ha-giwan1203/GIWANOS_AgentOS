# 클로드코드 hook 시스템 개선 실행계획 (2026-04-22)

> 2자 토론 (Claude × GPT) 2라운드 합의안.
> 로그: `debate_20260422_150445/round1_gpt.md`, `round1_claude_harness.md`, `round2_gpt.md`, `round2_claude_harness.md`
> 토론 의제: 전면 재설계 vs coverage 축소 → **coverage 축소 + 남는 핵심 contract형 재설계 하이브리드 채택**

## 핵심 원칙
1. "더 똑똑한 evidence"가 아니라 "evidence가 덜 필요하도록 구조를 줄이기"
2. 축 간 의존: **evidence 선행** → diagnostics → state → boundary
3. 1주차=계측 정비 + evidence coverage 축소 / 2주차=contract 재설계 + state 경량화 + boundary 테스트 승격

## 구조 분류 (4축)
- **evidence 축**: risk_profile_prompt / evidence_mark_read / evidence_gate / evidence_stop_guard — coverage 축소 + core 3종 contract화
- **상태 복원 축**: precompact_save / session_start_restore / state_rebind_check — 복원은 SessionStart 한 곳
- **진단/계측 축**: selfcheck / doctor_lite / hook_registry / gate_boundary_check — 검증기와 관측기 분리
- **게이트 경계 축**: block_dangerous / commit_gate / completion_gate / evidence_gate — grep → smoke 시나리오 승격

## 마커 분류
| 분류 | 마커 | 처리 |
|---|---|---|
| A. evidence-core 유지 | `date_check.ok` / `auth_diag.ok` / `identifier_ref.ok` | week1 coverage만 축소, week2 contract형 재설계 |
| B. instruction/control 유지 | `debate_entry_read` / `debate_claude_read` / `domain_<d>__<doc>` / `skill_read__<skill>` / `debate_send_gate` / `debate_independent_review` | evidence 축과 분리, 소속 gate 그대로 유지 |
| C. 삭제 후보 (week2) | `skill_read.ok`(단일) / `domain_read` / `tasks_read` / `handoff_read` / `status_read` | active gate 미참조 확인됨 (Claude 교차 검증) |

## 1주차 작업묶음

### 1. drift source 정리 (hook_registry 격하)
- 파일: `.claude/scripts/hook_registry.sh`, `.claude/hooks/list_active_hooks.sh`, `.claude/hooks/final_check.sh`, `.claude/hooks/README.md`, `90_공통기준/업무관리/STATUS.md`
- 변경: hook_registry.sh를 truth chain에서 제외 → list_active_hooks + final_check 단일 기준. hook_registry 폐기 또는 legacy 격하
- 소요: 30분~1시간 / 선행: 없음
- 검증: `list_active_hooks --count`와 `final_check` 기준 숫자 일치

### 2. selfcheck 24h 정확 집계
- 파일: `.claude/self/selfcheck.sh`
- 변경: `selfcheck.sh:75-77` CUTOFF prefix grep → 정확한 timestamp 비교
- 소요: 30분 / 선행: 없음
- 검증: 최근 24h 수치 = 독립 one-liner 계산 결과

### 3. doctor_lite fallback
- 파일: `.claude/hooks/doctor_lite.sh`
- 변경: `doctor_lite.sh:15` python3 하드의존 → smoke_fast:33 동일 패턴 fallback
- 소요: 15분 / 선행: 없음
- 검증: python만 설치된 환경에서도 정상 exit 0

### 4. evidence coverage 축소 (본 수술 1차)
- 파일: `.claude/hooks/risk_profile_prompt.sh`, `evidence_gate.sh`, `evidence_stop_guard.sh`, `evidence_mark_read.sh`, `smoke_test.sh`
- 변경 체크리스트 (Claude 교차 검증 추가):
  - (a) `evidence_gate.sh:112-140` tasks_handoff/tasks_updated/handoff_updated 검증 블록 제거 → commit_gate/completion_gate로 이관 (write_marker/after_state_sync 기반 책임 이미 존재)
  - (b) `evidence_gate.sh:186-203` + `risk_profile_prompt.sh:80-87` map_scope 블록 제거 (또는 별도 hook/commit_gate로 분리)
  - (c) `evidence_gate.sh:165-184` + `risk_profile_prompt.sh:61-64` skill_read 그룹 → skill_instruction_gate로 이관. identifier_ref는 evidence-core 유지
  - (d) `evidence_mark_read.sh:42-44` tasks_read/handoff_read/status_read mark 제거 (week2 삭제 후보 C분류 선행)
  - (e) smoke_test.sh에 회귀 테스트 추가 (tasks_handoff 책임 이관 검증)
- 소요: 반나절~1일 / 선행: 2, 3 완료
- 검증:
  - (1) commit 시 TASKS/HANDOFF 미갱신 차단이 **completion_gate**에서만 발생
  - (2) evidence_gate는 core 3종(date_check / auth_diag / identifier_ref) req만 감시
  - (3) 반영 후 7일 관찰: `evidence_gate` 7일 미해결 **50% 이하** (세션86 기준 272→136건)

## 1주차 검증 기준 (정량 지표)
- hook_registry 비활성 후 final_check 숫자 무결
- selfcheck 24h 집계 정확도 검증
- doctor_lite python fallback 작동
- **evidence_gate 7일 미해결 ≤ 136건** (세션86 실측 272건 대비 50% 감소 목표)
- **최근 24h 신규 incident < 이전 대비 +10%** (회귀 트립와이어, Claude 추가)

## 2주차 작업묶음 (1주차 관찰 데이터 수령 후 착수)

### 5. evidence 3종 contract형 재설계
- 파일: `risk_profile_prompt.sh`, `evidence_gate.sh`, `evidence_mark_read.sh`, `evidence_stop_guard.sh`, `README.md`
- 변경: date/auth/identifier 3종을 키워드+grep+suppression이 아닌 provider-contract로 전환. "무슨 텍스트를 읽었나" → "어떤 검증 행위를 했고 결과가 무엇인가"
- 소요: 1~2일 / 선행: 1주차 4번 완료 + 1주 관찰 데이터
- **조건부 진행**: 1주차 4번 반영 후 미해결 건수가 목표(136건) 미달성 시 5번 설계 재검토

### 6. 상태 복원 축 경량화
- 파일: `precompact_save.sh`, `session_start_restore.sh`, `state_rebind_check.sh`, `README.md`
- 변경: state_rebind_check를 content injection → detect-only 경고. precompact_save 얇게. SessionStart fallback 유지, 쓰기 직전 TASKS/HANDOFF 재주입 중단
- 소요: 반나절~1일 / 선행: 5번 권장, 최소 4번 완료

### 7. boundary 보증 smoke 시나리오 승격
- 파일: `smoke_test.sh`, `smoke_fast.sh`, `gate_boundary_check.sh`, 필요 시 `.claude/hooks/testdata/` 또는 `_fixtures/`
- 변경: gate_boundary_check는 lint 유지. smoke_test에 boundary 시나리오 6건(축1×2 / 축2×1 / 축3×2 + 추가) runtime 케이스 추가. smoke_fast에 1건 얹음
- 시나리오 카탈로그:
  - [축1] git push 단독 / 강한 완료 주장 + git dirty
  - [축2] git commit + evidence req 없음
  - [축3] 로그인 실패 결론 + auth_diag.req 미해결 / 완료 보고 + auth/date/id req 없음
- 소요: 반나절~1일 / 선행: 5, 6 완료

## 롤백 조건
- **1번**: hook_registry 제거 후 final_check 숫자 불일치 → legacy 격하 복귀
- **4번**: evidence coverage 축소 후 incident 증가 → 해당 req만 선택적 복구
- **5번**: contract 전환 후 false-negative 발생 → shorter excerpt로 복귀
- **7번**: 신규 smoke 케이스 flaky → 해당 케이스만 fixture 보강 전까지 제외, gate_boundary_check lint 유지

## 손대지 않기로 한 축 (재확인)
- `block_dangerous.sh` fail-closed 파괴 명령 차단
- `commit_gate.sh` final_check 소유권 / push-only skip
- `completion_gate.sh` 강한 완료 주장 + git/state sync
- `write_marker.json` / `after_state_sync` 계약
- SessionStart fallback (kernel stale/missing 시 TASKS/HANDOFF 원문)
- instruction/control 마커 계열 (B분류)
- fingerprint 키 정의 (week1 유지)

## 실행 전 확인 필요
- 사용자 승인 (Full Lane 수술 — hook 실행 흐름·판정 분기 변경)
- map-scope 정식 선언: 영향 범위 = evidence 축 4개 훅 + risk_profile_prompt + 2개 스킬 의존(debate_gate, skill_instruction_gate 간접)
- 각 단계 커밋 전 smoke_test 전수 통과 확인
- 단계별 개별 커밋 (1/2/3 개별, 4는 서브커밋 5개 내외)
