# Round 1 — Step 6-5: Claude 종합안 (4-way 대조)

**작성 시각**: 2026-04-27 20:46 KST
**기반**: round1_claude.md (6-0 독자) + round1_gpt.md + round1_gemini.md + round1_gemini_verify_gpt.md + round1_gpt_verify_gemini.md

---

## 결론 1줄

본 작업(모드 D 자동 진입 차단 정합화)은 양측 1·2·5번 만장 동의 + 안건 4 GPT 권장 표현 채택. 안건 3 반대·안건 4 보류·Gemini 추가제안은 모드 E 정책 영역으로 본 작업과 직교 → 별건 분리.

## claude_delta 자체 선언

`claude_delta = "partial"` — Claude 6-0 독자 답안 대비 다음 변경 발생:
- 안건 4 표현: GPT 보강 채택 ("수정·커밋 중단, 라벨 보고 후 대기" 명시)
- 안건 5 보강: Gemini "HANDOFF 수동 1줄 기록 강제" 채택 (자동 hook은 별건 분리 유지)
- 별건 의제 추가 등록: ERP/MES 트랜잭션 롤백·외부 CLI 래퍼 cross-grep·HANDOFF 미결 수동 기록

## issue_class
`issue_class = "B"` (구조·정책 변경)

## 6-5 skip 여부
`skip_65 = false` — B 분류이며 안건 3에서 양측 충돌 + 추가제안 평가 필요

---

## 안건별 채택/보류/버림

### 안건 1 — 누락 검토 대상 추가 여부 ✅ 채택
- 양측 동의. Gemini 권고 "외부 CLI 래퍼 스크립트 은닉 여부 cross-grep" → **부분 채택**.
- 결정: 본 작업 직전 grep 한 번 더 수행해 외부 CLI/래퍼·`.claude/scripts/`·`.claude/agents/` 자동 D 진입 명문 확인. 미발견 시 plan 그대로 진행.

### 안건 2 — share_gate.sh 정합성 ✅ 채택
- 양측 동의 (Claude 입장 정합). 분배 정책으로 직교 유지 확정.

### 안건 3 — 세션 캐싱 시점 부정합 ⚠️ 채택 (Claude 입장 + Gemini 우려 흡수)
- GPT 동의 / Gemini 반대 / GPT 검증에서 "Gemini는 모드 E 영역 끌어옴" 지적
- **Claude 결정**: 임시 가드 hook 신설은 본 범위 초과(C 강제 승격 트리거). **HANDOFF에 수동 1줄 메모로 흡수**:
  - "본 세션 종료 전까지 share-result 호출 시 자동 D 승격 가능성 잔존 — 수동 모니터링 필요"
- 다음 세션 활성으로 충분. 임시 hook 추가는 폐기.

### 안건 4 — NEVER 추가 라인 형식 ✅ 채택 (GPT 표현)
- GPT 권장: `[NEVER] B 감지 라벨 없이 단독 반영 금지. 사용자 명시 호출이 없으면 수정·커밋은 중단하고, B 감지 라벨과 대기 상태만 보고한다.`
- Gemini 보류 (ERP 트랜잭션 롤백)는 모드 E 영역 → 별건 분리
- **share-result.md에 GPT 표현 그대로 추가**

### 안건 5 — 의제 표류 보호 메커니즘 ✅ 채택 (사용자 책임 + Gemini HANDOFF 흡수)
- 양측 동의. Gemini "대기 진입 직전 HANDOFF.md 미결 수동 기록 강제" → **부분 채택**.
- 자동 등재 hook은 별건 분리 유지
- **share-result.md B 분기 절차에 추가**: "B 감지 라벨 표기 후 사용자 결정 대기 시, HANDOFF.md에 미결 의제 1줄 수동 기록 권장"

---

## 별건 등록 (본 작업 범위 외)

1. **ERP/MES 트랜잭션 롤백 NEVER 조항** (Gemini 추가제안)
   - 분리 사유: 모드 E (장애 복구) 정책 영역. 본 작업은 모드 D (토론 진입 정책).
   - 검토 위치: `04_생산계획/CLAUDE.md` 또는 `90_공통기준/erp-mes-recovery-protocol.md` (세션116 별건 4번과 합쳐 검토)
   - 우선순위: 세션116 별건 4번 PLC 인터치·Staging Table 청소와 통합

2. **외부 CLI 래퍼·`.claude/scripts/`·`.claude/agents/` cross-grep 검증** (Gemini 안건 1 권고)
   - 분리 사유: 본 작업 plan 작성 단계에 1회 cross-grep 후 결과 plan 보강에 포함 (별건 아님 → 본 작업 직전 수행)

3. **임시 가드 hook 신설 검토** (Gemini 안건 3 반대)
   - 분리 사유: hook 신설은 C 강제 승격 트리거. 본 작업 hook 신설 금지 원칙 (세션116 별건 2번 R1~R5 Pre-commit hook과 동일 영역)
   - 통합 검토: 별건 의제 2번 (R1~R5 Pre-commit hook)과 묶어 hook 신설 정책 토론 시 동시 검토

---

## pass_ratio 계산

| 검증 키 | 결과 |
|---------|------|
| `gemini_verifies_gpt` | 동의 (1) |
| `gpt_verifies_gemini` | 검증 필요 (0) |
| `gpt_verifies_claude` | 6-5 단계에서 수령 예정 |
| `gemini_verifies_claude` | 6-5 단계에서 수령 예정 |

- 현재 누적: 1/2 (50%) — 6-5 양측 검증 후 4/4 단위로 재계산
- 채택 임계값: pass_ratio ≥ 2/3 (≥ 0.67)

## 4-way 대조 표

| 안건 | Claude(6-0) | GPT | Gemini | 종합 결정 | 합의 강도 |
|------|------------|-----|--------|-----------|-----------|
| 1 | 실증됨/동의 | 실증됨/동의 | 실증됨/동의 (cross-grep 권고) | 채택 + cross-grep 추가 | 만장 |
| 2 | 실증됨/동의 | 실증됨/동의 | 일반론/동의 | 채택 | 만장 |
| 3 | 환경미스매치/임시 가드 불필요 | 환경미스매치/동의 | 환경미스매치/반대 | Claude 입장 + HANDOFF 메모 흡수 | 2/3 (Gemini 우려 흡수) |
| 4 | 실증됨/동의 (표현 보강 필요) | 구현경로미정/보류 → A 추가제안 | 구현경로미정/보류 (ERP 영역) | GPT 표현 채택 | 2/3 |
| 5 | 환경미스매치/별건 분리 | 일반론/동의 | 메타순환/동의 (HANDOFF 권고) | 채택 + HANDOFF 1줄 흡수 | 만장 |

## 반영 예정 변경 사항 (plan.md 갱신)

1. **토론모드 CLAUDE.md 줄 79-122** — "B 분류 감지 + 보고 (비대칭 전환)"으로 재기록
2. **share-result.md 줄 173-186** — "B. 구조 변경 감지 — 라벨 표기 + 사용자 호출 대기"로 변경
3. **share-result.md** — `[NEVER] B 감지 라벨 없이 단독 반영 금지. 사용자 명시 호출이 없으면 수정·커밋은 중단하고, B 감지 라벨과 대기 상태만 보고한다.` 추가
4. **share-result.md** — "B 감지 라벨 표기 후 사용자 결정 대기 시, HANDOFF.md에 미결 의제 1줄 수동 기록 권장" 라인 추가
5. **HANDOFF.md** — 본 세션 종료 시점에 "본 세션 종료 전 share-result 호출 시 자동 D 승격 가능성 잔존" 1줄 메모 (추후 다음 세션 활성 후 삭제)
6. **plan.md "토론 결과 반영 자리"** — Round 1 채택 5건 + 별건 3건 채워 넣기
7. **별건 등록**: ERP/MES 트랜잭션 롤백 (모드 E 영역, 세션116 별건 4번과 통합), 임시 가드 hook (세션116 별건 2번과 통합)
8. **사전 cross-grep**: `.claude/scripts/`·`.claude/agents/`·외부 CLI 래퍼 자동 D 진입 명문 검색 (구현 직전 수행)
