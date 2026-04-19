# Round 1 — Claude 종합 설계안 (최종 — 수정 반영 버전)

## 의제
클로드코드(Claude Code) 운영 정밀 분석 — 3자 토론 Round 1

## 양측 수정 제안 통합

### GPT 제안
1. "측정 프로토콜 확정" 단계 선행 — true_positive / FP 의심 / 정상중간과정 라벨링 규칙 고정
2. evidence_gate를 하위 정책별(tasks_handoff / skill_read / map_scope / auth_diag)로 분해 분석

### Gemini 제안
1. 파이프라인 순서 명시적 강제 — Policy 재검토 통과 후에만 과거 ledger 정리 실행

→ 두 제안은 **상호 보완** (측정 → 재정의 → 통과 시 정리)

---

## 최종 설계안 (채택 버전)

### 즉시 실행 (세션75+ — 엄격 시퀀스)

#### Step 1-a. 측정 프로토콜 확정 (GPT 제안 반영)
- 라벨링 규칙 3종 고정:
  - `true_positive`: 실제 정책 위반·실무 손실 유발
  - `false_positive_suspect`: 정책 조건은 맞으나 현업 워크플로우에서는 자연스러운 중간 상태
  - `normal_intermediate`: 정책 재설계가 필요한 구조적 경고
- 게이트별 표본 기준 정의 (예: evidence_gate 100건 샘플 수동 분류)
- 산출물: `.claude/docs/incident_labeling_protocol.md`

#### Step 1-b. evidence_gate Policy 하위 분해 분석 (GPT 제안 반영)
- evidence_gate.sh 현재 조건 분해:
  - `tasks_handoff.req` 정책
  - `skill_read.req` 정책
  - `identifier_ref.req` 정책
  - `map_scope.req` 정책
  - `auth_diag.req` 정책
- 각 정책별 evidence_missing 526건 중 비율 산출
- 각 정책별 true_positive 비율 정밀 측정 (Step 1-a 기준)

#### Step 1-c. evidence_gate Policy 재정의
- 관점: **"게이트 완화" 아닌 "기준 재정의"** (GPT 방향)
- 하위 정책 중 false_positive rate 가장 높은 것부터 재설계
- 현업 G-ERP 워크플로우 실제 요건과 교차 검증

#### Step 2. (Step 1 통과 후에만) incident_ledger 반복 5종 정리 (Gemini 순서 강제)
- 대상 (872건 미해결 중 상위 5종):
  - evidence_gate: 474
  - commit_gate: 259
  - navigate_gate: 69
  - completion_gate: 52
  - skill_instruction_gate: 49
  - **합계: 903건 (87.9%)**
- `resolved=True` 트리거 기준 명확화
- 재발 방지 정책 체크

#### Step 3. 문서 드리프트 자동 --fix 금지 + 파생 문서 preview 절충 (병렬 가능)
- 상태 원본 (STATUS/TASKS/HANDOFF): **수동 판정만 허용**
- 파생 문서 (README/AGENTS_GUIDE):
  - diff preview 생성 → 사용자 확정 후 적용
  - 자동 덮어쓰기 금지

### Round 2 의제 (별도 토론)

#### Policy-Workflow Mismatch 종합 감사
- 제조업 G-ERP 실제 워크플로우 단계 vs 게이트 Policy 맵핑
- true_positive 비율이 구조적으로 낮은 이유 규명 (1.2%)
- 게이트별 False Positive / Negative rate 측정 체계 설계
- 현업 사용자 인터뷰·실무 데이터 기반 기준 재검토

#### debate_verify 체인 점검 (Gemini 주장 채택)
- result.json 파싱 실패 반복 원인 분석
- step5_final_verification.md 누락 원인
- Round 2 결과의 메타 신뢰성 확보 필수 근거
- 현재 incident 18건 잔존 → 7일 0건 조건 별도 이슈

### 버림 (Round 2 제외 — 양측 합의)
- 주장 4 hook_common.sh fragility (설계자 자각 주석 L79 + 장애 사례 0)
- 주장 5 python3 portable (warn 31건 차단 없음, 환경 가정 유지)

---

## Round 1 인사이트 (3자 토론 실효성 검증)

1. **상호 감시 프로토콜 작동 확인** — GPT 주장 3(60분 캐시)이 Claude·Gemini 2:1 이의 → GPT 자진 철회. 단일 모델 오류 자동 차단 실증.
2. **3자 기여 차별화 성공** — GPT(문제 식별 + 표현 세련화) / Gemini(독립 각도 + 근본 정책 관점) / Claude(실물 검증 + 종합 설계). 도메인 한정 없이 강점 기반 분담.
3. **incident 1027건 breakdown이 결정적 증거** — true_positive 1.2% 수치가 Gemini "Policy 현실성" 지적을 실증. 추상 주장 → 수치 실증으로 신규 의제 승격 정당화.

## 최종 결과
- **채택 (pass_ratio 1.00, round_count 1/3)**
- Round 1 종결, Round 2 의제 확정
- 세션75 이월: Step 1-a부터 엄격 시퀀스로 실행
