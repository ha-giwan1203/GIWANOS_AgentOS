# Round 1 — Claude 종합 설계안

## 실측 분석 (Claude 독립)

### evidence_missing 333건/7일 세부 집계
| Detail 패턴 | 건수 | Hook | 성격 |
|---|---|---|---|
| map_scope.req 존재 | 99 | evidence_gate | 현재 로직 (hook/settings 편집 대상 축소됨) |
| skill_read/identifier_ref.req | 86 | evidence_gate | 현재 로직 (SKILL.md 미독 차단) |
| tasks_handoff.req | 63 | evidence_gate | 구버전 로그 + 현재 commit-only 검증 혼재 |
| MES access without SKILL.md read | 60 | skill_instruction_gate | 현재 로직 (MES 접근 전 SKILL 강제) |
| commit 차단 | 16 | evidence_gate | 현재 로직 |

- 2026-04-19 **165건** (50%): 세션71~75 대량 작업일 (의제5 3자 토론, 세션72 Phase 2-B 등)
- 2026-04-14 **64건** (19%): 세션66 3자 토론 + 구버전 tasks_handoff 잔존 시점

### 양측 하네스 분석 (채택/보류/버림)

**채택 (5건)**:
1. [GPT 실증] 구버전 tasks_handoff 패턴 + 현재 map_scope 반복 + commit 시점 차단 **혼재** → 실측과 정합
2. [GPT 실증] 워크플로우 자동 충족 > gate 조건 완화 우선순위 → evidence_mark_read.sh 범위 확장 방향 타당
3. [GPT 실증] 재집계 시작점 = 세션81 수정 커밋 시점 → debate_verify.sh 헤더 방어코드 반영 근거
4. [Gemini 과잉설계→검증필요] Gate 탐지 정규식 범위 과다 가능성 → 의제 1 후속 분석 대상
5. [Gemini 실증] Phase 2-C "검증 기간" 정의 (영문/특수문자/한글 경로 회귀 테스트 포함)

**보류 (1건)**:
- [Gemini 일반론] HISTORY.md 통합 방안 — 현 시점 A(아카이브) 실행 후 필요 시 후속 판단

**버림 (0건)**

## Claude 최종 설계안

### 의제 1 — evidence_gate 과다 발화 (후속 세션 이월)
**즉시 조치 없음.** 근거:
- GPT "검증 필요" + Gemini "검증 필요" → pass_ratio 0.00 (양측 검증 필요)
- 333건 detail 분포 확보. 후속 3자 토론 라운드에서 별도 의제로 진행
- 이번 세션에서 `evidence_mark_read.sh` 범위 확장 또는 정규식 재검토는 구현 안 함

**TASKS 이월 안건**:
1. evidence_mark_read.sh 자동 충족 범위 확장 (TASKS/HANDOFF 수정 흔적 + SKILL.md 읽기 + map_scope 완료 마커 연쇄 적립)
2. evidence_gate 정규식 범위 재검토 (특히 multi-domain 워크플로우에서 오탐 여부)
3. 구버전 tasks_handoff 로그 vs 현재 commit-only 검증 로그 분리 재집계

### 의제 2 — 생산계획자동화 아카이브 이동
**즉시 실행 완료**
- `90_공통기준/스킬/생산계획자동화/` → `98_아카이브/생산계획자동화_구버전_20260420/`
- 파일 3건 이동: 변경이력·운영절차·자동화규칙 v3.0
- 활성 스킬 `sp3-production-plan/SKILL.md` 유지
- pass_ratio = 2/2 (양측 동의)

### 의제 3 — debate_verify.sh Phase 2-C 승격 준비
**즉시 실행: 헤더 문서화만** (exit 2 전환은 7일 후)
- `debate_verify.sh` 헤더에 Phase 2-C 조건 주석 추가:
  - 재집계 시작점: 세션81 수정 커밋 SHA 408c4856 (2026-04-20 ~10:54 KST)
  - 관찰 기간: post-fix 7일 연속 type=debate_verify 0건
  - 회귀 테스트 요건: 영문/특수문자/한글 경로 커버 (Gemini 제안 반영)
  - 승격 방식: hook_gate 래퍼 + exit 2 + JSON decision=deny (기존 Phase 2-B 6종 준용)
  - 평가 시점: 2026-04-27 세션89+ 예상
- pass_ratio = 2/2 (양측 동의, 단 Gemini 회귀 테스트 보강 반영)

## pass_ratio 집계

| 의제 | gpt_verifies_gemini | gemini_verifies_gpt | gpt_verifies_claude | gemini_verifies_claude | pass_ratio |
|---|---|---|---|---|---|
| 1 | — | 동의 | (Step 5 대기) | (Step 5 대기) | 0.33 (검증 필요 다수) |
| 2 | — | 동의 | (Step 5 대기) | (Step 5 대기) | 0.33 (amount to pass) |
| 3 | — | 동의 | (Step 5 대기) | (Step 5 대기) | 0.33 (amount to pass) |

> Round 1에서 Gemini → GPT 검증만 확보. Step 5 최종 검증에서 양측 재판정 받을 예정.
> 의제 2·3은 양측 본론 판정 수렴(동의) → Round 2 없이 Step 5 진행.
> 의제 1은 양측 "검증 필요" → 이번 세션 조치 유보, 별건 이월.

## 진행 결정
- Step 5 (산출물 커밋 + 양측 최종 검증) 즉시 진행
- 커밋 태그: `[3way]`
- 커밋 범위: 의제 2(폴더 이동) + 의제 3(헤더 문서화) + TASKS/HANDOFF 갱신 + Round 1 로그 3건
