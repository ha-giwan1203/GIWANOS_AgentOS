# smoke_test Pruning 후보 선별 (Step 1)

> 세션77 착수. 3자 토론 Round 2 Step 1 Test Pruning 실행. GPT "격리 후 1주 관찰 후 삭제" + Gemini "과잉 검증 다이어트" 채택.

## 배경

세션76 Round 2에서 다음 합의:
- 167개 테스트 케이스 전수 실행은 Windows Git Bash에서 3m20s 소요
- Step 2(regression/capability 분할)로 commit 경로는 이미 smoke_fast만 실행(15.9s)
- capability 19섹션은 "수동 전체 검증"에만 사용 (`SMOKE_LEVEL=full`)
- 더 나아가 **capability 내부에서도 과잉 검증 다이어트** — 본 Step 1

## 선별 기준 (3자 합의)

### Pruning 제외 조건 (보호 유지)
1. **공용 의존성**: hook_common.sh / evidence_gate.sh / commit_gate.sh / completion_gate.sh 의존 시 보호가치 높음 (GPT 보강)
2. **고밀도 체크**: check_count ≥ 4는 구조적 의미 있는 assertion으로 간주, 보호
3. **30일 미관찰**: 본 항목은 현 데이터 부족(세션76 기준선)으로 미적용 — 세션79+ 재평가

### Pruning 후보 조건 (격리 → 1주 관찰 → 삭제 판정)
- capability 섹션
- 외부 훅 비의존 또는 단일 hook 의존 (공용 축 제외)
- check_count ≤ 3 (저밀도)

## 선별 결과 — Capability 19섹션 중 7섹션 격리 후보 (36.8%)

### quarantine_1 (1순위 격리 — 외부 훅 비의존 + 저밀도)

| 섹션 | 제목 | checks | hooks |
|------|------|--------|-------|
| **24b** | json_escape payload 검증 | 3 | (없음) |
| **33** | incident_review.py | 3 | (없음) |
| **34** | classify_feedback.py | 3 | (없음) |
| **36** | hook_config.json task_escalation | 3 | (없음) |
| **37** | incident_repair.py 세션40 매핑 | 3 | (없음) |
| **38** | task_runner.sh | 3 | (없음) |
| **39** | incident_repair.py backfill | 2 | (없음) |

**합계**: 7섹션 / 20 checks (총 167 중 12.0%)

### protect (보호 유지 — 13섹션)

| 섹션 | 제목 | checks | 보호 사유 |
|------|------|--------|----------|
| 22 | 토론모드 selector 문서 정합성 | 5 | high_checks |
| 23 | 토론모드 Chrome MCP 단일화 | 7 | high_checks |
| 24 | safe_json_get escape 회귀 | 2 | common_dep(hook_common) |
| 31 | circuit_breaker_tripped | 3 | common_dep(commit_gate, hook_common) |
| 32 | instruction_read_gate | 10 | high_checks |
| 35 | hook_common.sh task_result | 3 | common_dep(hook_common) |
| 40 | commit_gate.sh 실행 테스트 | 4 | common_dep(commit_gate) |
| 41 | completion_gate.sh 실행 테스트 | 2 | common_dep(completion_gate) |
| 42 | evidence_gate.sh 실행 테스트 | 2 | common_dep(evidence_gate) |
| 43 | completion_gate deny-path | 2 | common_dep |
| 44 | evidence_gate deny-path | 6 | common_dep + high_checks |
| 45 | navigate_gate.sh 런타임 | 6 | high_checks |
| 46 | 세션51 런타임 테스트 | 5 | common_dep(completion_gate, hook_common) |

## 관찰 절차 (GPT 제안 채택)

### Phase 1: 격리 표시 (세션77, 본 세션 — 코드 변경 없음)
- 본 문서에 후보 7섹션 명시
- 실제 smoke_test.sh 변경 없음 (여전히 `SMOKE_LEVEL=full` 시 실행됨)
- 목적: **관찰 기간 중 실제 사용자가 해당 섹션 체크에 의존하는 사건 발생 여부** 모니터링

### Phase 2: 1주 관찰 (세션77~세션84)
- 관찰 지표:
  - `SMOKE_LEVEL=full` 실행 횟수 (사용자 수동 검증 빈도)
  - 격리 후보 7섹션에서 FAIL 발생 여부 (현재 0)
  - incident_ledger에 관련 hook 실패 기록 여부
- 수집 위치: `hook_log.jsonl` + `incident_ledger.jsonl`

### Phase 3: 삭제 판정 (세션85 or 1주 후)
- 조건 A (전부 충족): 해당 섹션 FAIL 0 + `SMOKE_LEVEL=full` 실행 1회 이상 + incident 증가 없음
  - → **smoke_test.sh에서 실제 블록 삭제** (코드 변경)
- 조건 B (하나라도 실패): 보호로 환원
- 조건 C (관찰 데이터 부족 — `SMOKE_LEVEL=full` 실행 0회): 관찰 기간 연장

## 격리 ≠ 삭제 원칙 (안전 bias)

- 본 Phase 1에서는 **코드 한 줄도 삭제하지 않음**
- Phase 3까지 1주 확보 후 실제 삭제
- 삭제 시에도 `90_공통기준/토론모드/logs/`에 삭제 전 섹션 블록 전문 아카이브

## Silent Failure 대응 (Gemini 경고 반영)

격리 후보 7섹션 중 파이썬 도구(`incident_review.py`, `classify_feedback.py`, `incident_repair.py` 등) 관련이 5섹션.
이들이 `SMOKE_LEVEL=full`에서만 돌고 평소에는 조용히 고장날 위험 있음.

→ **세션77+ 이월**: `capability` 자동 사후 검증 스크립트 (일일 배치)
- `.claude/hooks/nightly_capability_check.sh` 신설 후보 (Windows schtasks)
- 본 문서 Phase 3 이전에 **반드시 구현**되어야 격리 후보 삭제 진행 가능

## 예상 효과

| 단계 | 테스트 수 | 예상 시간 (SMOKE_LEVEL=full) |
|------|----------|------------------------------|
| 현재 | 167 | 3m 20s |
| Phase 3 삭제 완료 | 147 | 약 2m 55s (12% 단축) |

본 감축은 commit 경로(SMOKE_LEVEL=fast)와 무관. 수동 전체 검증 시간만 단축.

## 연관 문서

- 3자 토론 Round 2: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/round2_*.md`
- Step 2 구현: `.claude/hooks/final_check.sh` L351-380 (SMOKE_LEVEL 분기)
- 세션76 HANDOFF: `90_공통기준/업무관리/HANDOFF.md` §0
