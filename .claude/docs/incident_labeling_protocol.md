# Incident Labeling Protocol (Step 1-a)

> 세션75 3자 토론 Round 1 채택 (`debate_20260419_215501_3way`) 후속 — GPT 수정 제안 "측정 프로토콜 확정" 반영.
> 목적: evidence_gate Policy 재정의 **전에** incident를 세 라벨로 정확히 분류해서 "무엇을 바꿔야 하고 무엇을 유지해야 하는지" 판단 근거 확보.
> **이 문서는 Step 1-b/1-c/2 실행의 사전 조건.** 이 프로토콜 없이 게이트 기준을 건드리면 진짜 통제까지 무너질 수 있다(GPT 경고).

---

## 1. 라벨 정의 (3종)

### A. `true_positive` — 실제 정책 위반·실무 손실 유발
- 설명: 게이트가 **정확히 잡아낸** 진짜 문제. 이 훅이 없었으면 실무 손실(잘못된 커밋·오작동·오판정) 발생했을 것.
- 판정 기준:
  - (a) 차단/경고 대상이 실제 규칙 위반 (예: 미검증 xlsx 덮어쓰기, 미읽은 CLAUDE.md 상태에서 ChatGPT 진입)
  - (b) 해당 incident로 실제로 작업 흐름이 중단되고 **올바르게 수정 후 재진행**한 기록 존재
  - (c) 재발 시에도 동일하게 차단되어야 함
- 조치: **유지** (Policy 변경 금지)
- 예시 후보:
  - `MES access without SKILL.md read` (스킬 지침 미읽기 상태로 MES 접근 시도)
  - `date_scope_guard` 차단 (날짜 규칙 위반 — 계산 오차 방지)

### B. `false_positive_suspect` — 정책 조건은 맞으나 현업 워크플로우에서는 자연스러운 중간 상태
- 설명: 게이트가 **과도하게 민감**하게 잡아낸 것. 조건식상 위반이지만, **제조업 G-ERP 실무 워크플로우의 정상 중간 단계**에서 필연적으로 발생하는 상태.
- 판정 기준:
  - (a) 같은 세션/작업 맥락에서 **곧바로 자연스럽게 해소됨** (예: 다음 작업 단계에서 파일 갱신 발생)
  - (b) **재발 패턴**이 존재하고 사용자가 수정 없이 넘어가도 실무 손실 없음
  - (c) Policy 조건이 **제조업 실무 자연 흐름**과 **mismatch**
- 조치: **Policy 완화·세분화·조건 재정의** 대상
- 예시 후보:
  - `STATUS(2026-04-18) < TASKS(2026-04-19) 드리프트` — 작업 중 TASKS만 먼저 갱신되고 STATUS는 다음 단계에서 반영되는 자연 흐름
  - `tasks_handoff.req 미해결` — 작업 진행 중 handoff 준비 단계에서 발생
  - `evidence_missing` (일부) — 실물 검증은 다음 Step에서 진행하는 시퀀스 특성

### C. `normal_intermediate` — 정책 재설계가 필요한 구조적 경고
- 설명: 게이트가 찍는 것이 **정확한 에러도 아니고 자연스러운 중간 상태도 아닌**, 시스템 자체의 **구조적 측정 실패**. 라벨링만 되고 조치는 무의미.
- 판정 기준:
  - (a) incident는 기록되나 **resolve 조건이 불명확**하거나 **자동으로 resolved=True 전환되지 않음**
  - (b) 동일 detail 내용이 **반복 발생**하지만 수정/변경 가능 요소 부재
  - (c) 단순 계측성 이벤트로 gate 역할 자체가 없음
- 조치: **incident 기록 중단** 또는 **advisory/measurement 등급으로 재분류**
- 예시 후보:
  - `pre_commit_check` (216건) — 커밋 전 경고만이고 실제 차단 아닌 경우
  - `structural_intermediate` (45건) — 라벨 자체가 이미 "구조적 중간"임을 명시
  - `python3_dependency warn` (31건) — 경고만 반복, 차단 없음

---

## 2. 데이터 소스

- **원본 파일**: `.claude/incident_ledger.jsonl` (1027건)
- **주요 필드** (분류 판단 시 활용):
  - `ts` — 타임스탬프 (재발 패턴 확인용)
  - `hook` — 발생 훅
  - `file` — 대상 파일 (비어있는 경우 많음)
  - `detail` — 구체 내용 (핵심 판단 기준)
  - `classification_reason` — 기존 시스템 분류 (예: `evidence_missing`, `pre_commit_check`, `true_positive` 등)
  - `resolved` — 해결 여부 (현재 True 155 / False 872)
  - `normal_flow` — 자연 흐름 여부 플래그 (일부 incident에 이미 포함)
  - `source` — 어느 검사에서 나왔는지 (예: `final_check`, `gpt-read`)
  - `warn_raw` — 원본 경고 메시지

---

## 3. 표본 정책

### 샘플 크기
- **Step 1-a 본 프로토콜 확정 후 첫 샘플**: **evidence_gate 전수 474건** 중 **최근 100건** 수동 분류
  - 최근 100건: `ts` 기준 내림차순 정렬 후 상위 100
  - 이유: 오래된 incident는 맥락 재구성이 어렵고, 최근 Policy 상태 반영이 필요
- 이후 Step 1-b에서 하위 정책(tasks_handoff / skill_read / map_scope / auth_diag / identifier_ref)별 비율 산출 시 전수 474건 기준

### 분류 방법
- 수동 분류 우선 (Claude가 detail + classification_reason + resolved + ts 종합 판단)
- 판정 애매한 것은 **`ambiguous` 4번째 라벨**로 분리 (규칙 보완 후 재분류)
- 분류 결과 저장 위치: `.claude/docs/incident_labels_evidence_gate_100.json`

### 분류 스키마
```json
{
  "ts": "2026-04-19T...",
  "hook": "evidence_gate",
  "detail": "...",
  "classification_reason_original": "evidence_missing",
  "resolved": false,
  "new_label": "true_positive|false_positive_suspect|normal_intermediate|ambiguous",
  "reason": "1문장 분류 근거",
  "policy_key": "tasks_handoff|skill_read|map_scope|auth_diag|identifier_ref|other"
}
```

---

## 4. 분류 판단 규칙 (Tiebreaker)

라벨 결정이 애매할 때 순서대로 적용:

1. **해결 상태 우선**: `resolved=True`이고 사용자가 명시적 조치한 기록 있으면 → `true_positive`
2. **자연 흐름 플래그**: `normal_flow=true` 필드가 있으면 → `false_positive_suspect` 후보
3. **재발 빈도**: 같은 `detail` 3회 이상 반복 + 전부 미해결 → `normal_intermediate` 또는 `false_positive_suspect`
4. **차단 vs 경고**: `type=gate_reject`는 강한 차단, `type=warn_recorded`는 경고 → 차단일수록 `true_positive` 가능성 높음
5. **분류 근거 미정**: 3개 규칙 모두 미매칭 → `ambiguous` (보류)

---

## 5. 검증 절차

분류 완료 후:
1. `true_positive` / `false_positive_suspect` / `normal_intermediate` / `ambiguous` 각 카운트 + 비율 산출
2. 기존 classification_reason (시스템 자동 분류)과 신규 라벨의 **교차 분포표** 생성
3. `policy_key`별 비율 분포 → Step 1-b evidence_gate 하위 분해 실측 근거로 사용
4. `ambiguous` 비율이 20% 초과 시 규칙 4장 보완 후 재분류

---

## 6. 경계 조건

- 분류는 **1회용이 아닌 기준선**. 향후 incident 발생 시 동일 프로토콜 적용
- Policy 재정의 후 **재측정 의무** — Step 1-c 재정의 → Step 2 실행 전/후 비율 변화 추적 필수
- `true_positive` 비율이 **목표치 10% 이상**으로 올라오면 Policy 재정의 성공 (현재 1.2%)
- 본 문서는 **고정 기준**. 수정 시 버전업 이력 기록 필수

---

## 7. 버전 이력

- v1.0 (2026-04-19 세션76): 초안 — 3자 토론 Round 1 GPT 제안 반영

---

## 8. 연관 문서

- 3자 토론 Round 1 로그: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/`
- 실물 검증: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/round1_reality_check.md`
- Round 1 종합 설계안: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/round1_claude_synthesis.md`
