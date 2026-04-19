# Round 2 — Claude 종합 설계안 (수정 반영 최종 버전)

## 의제
클로드코드 Policy-Workflow Mismatch 의제의 2호 구체 사례 — `smoke_test.sh` 3분 20초 병목 근본 해결

## 양측 수정 제안 통합

### GPT 제안 (Round 2 최종 검증)
1. Step 1 (c) "중복/저가치 삭제" → **"격리 후보로 분리 → 1주 관찰 후 삭제"** (안전 bias)
2. Pruning 기준 보강 — "30일 무고장"만 아니라 **최근 수정 이력 + 공용 의존성**(hook_common.sh, evidence) 고려

### Gemini 제안 (Round 2 최종 검증)
1. Step 2 capability 분할 후 **Silent Failure 방지** — 언제/어떻게 강제 실행? (일일 배치, 브랜치 병합 전 훅 등) 자동화된 사후 검증 계획 필요

→ 두 제안은 **상호 보완** (삭제 안전성 강화 + 사각지대 방지)

---

## 최종 설계안 (채택 버전)

### 실행 순서 (5단, 양측 보강 반영)

#### Step 1. Test Pruning (Gemini 제안 + GPT 수용 + 양측 보강)
- **3분류**:
  - (a) 커밋 필수 회귀: 유지
  - (b) full 전용 구조 검증: 유지
  - (c) **격리 후보 — 1주 관찰 후 삭제 판정** (GPT 안전 bias)
- **Pruning 기준**:
  - 30일 무고장 (1차)
  - **최근 수정 이력(해당 훅/공용파일 변경 빈도)** (GPT 보강)
  - **공용 의존성 여부**(hook_common.sh, evidence 물고 있으면 보호가치↑) (GPT 보강)
- 산출: `.claude/docs/smoke_test_pruning_candidates.md` (격리 후보 리스트)

#### Step 2. regression/capability 실행 분할 (GPT + Gemini 합의)
- **commit 경로**: regression만 실행 (`SMOKE_LEVEL=fast` 기본값)
- **--full-deep 또는 수동**: capability 포함 (`SMOKE_LEVEL=full`)
- **Silent Failure 방지** (Gemini 보강):
  - capability 자동 사후 검증 — 일일 배치 또는 브랜치 병합 전 훅
  - 실행 위치: 세션77+ 이월 (본 세션은 `SMOKE_LEVEL` 분기 구현까지)
  - 임시 가드: TASKS/HANDOFF에 "capability 수동 검증 1주 주기" 기록 (Silent Failure 완전 차단은 자동화 전까지 사용자 인지로)

#### Step 3. 섹션별/의존파일별 해시 캐시 (3자 합의, 세션77+)
- 섹션별 입력 파일 의존성 맵 정의 (예: 43-44 → hook_common.sh + evidence)
- 변경 없는 섹션은 스킵
- 기존 TTL 30분 전체 캐시는 "안전망"으로만 유지

#### Step 4. grep/sed 중복 통합 (3자 동의, 세션77+, 저공수)
- 같은 파일 연속 grep -q 반복 → 단일 awk/grep -f

#### Step 5. A안 (섹션별 보조 러너) — 최후순위, 조건부
- "섹션별 보조 러너 + PASS/FAIL 형식 유지" 조건 (블랙박스화 최소화)

## 버림 (3자 합의)
- 병렬화 xargs -P (MSYS2 안티패턴)

## 기존 조치 평가
- Claude 구현 "결과 캐시 TTL 30분": **안전망 유지**, 주 판정은 Step 3(섹션별 해시)로 교체 (세션77+)

## 측정 계획
- 각 단계 적용 후 `time bash final_check.sh --full` 실측
- 목표: 3m 31s → 30s 이하
- **세션76 Step 2 적용 후 실측**: **15.9s** (92% 단축 달성)

## 적용 세션 배분
- **세션76 (본 세션) 완료**:
  - Step 2 구현 (final_check.sh에 SMOKE_LEVEL 분기, 기본값 fast)
  - commit_gate push 단독 스킵 (Policy-Workflow Mismatch 1호 해결)
  - smoke_test 결과 캐시 로직 (안전망)
  - Round 2 로그 전체
- **세션76 Step 1 이월** (문서화만, 실제 격리는 세션77):
  - Pruning 후보 리스트 작성 — 공수 이슈로 세션77
- **세션77+ 이월**:
  - Step 1 실제 격리 + 1주 관찰
  - Step 3 섹션별 해시 캐시
  - Step 4 grep/sed 통합
  - Step 2 Silent Failure 자동화 (일일 배치)
- **Step 5**: 조건부 미래

---

## Round 2 인사이트 (3자 토론 재작동)

1. **Round 1과 동일 패턴 재현** — GPT 오판(A안 최우선) → Gemini 이의 + 신규 지적(Test Pruning) → GPT 자진 철회. 상호 감시 프로토콜 실증 2회차.
2. **Gemini 기여가 결정적** — Test Pruning + Silent Failure 2중 지적. "167 PASS를 성역 취급하지 말라"는 근본 관점이 본 의제의 본질 전환점.
3. **세션76 즉시 15.9s 달성** — Step 2 1개 적용으로 3m31s → 15.9s (92% 단축). Gemini "Low-Hanging Fruit" 논리 검증됨. 나머지 Step 3·4는 추가 효과를 위한 옵션으로 전락.

## 최종 결과
**채택 (pass_ratio 1.00, round_count 1/3 — Round 2도 1회차에 합의)**
세션76 Step 2 완료, Step 1·3·4 세션77+ 이월.
