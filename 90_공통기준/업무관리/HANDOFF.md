# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-20 KST — 세션79 (영상분석 드리프트 보정: token-threshold-warn Phase 1 실물 구현)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-20 세션79 — 영상 분석 적용 점검 및 드리프트 보정)

### 사용자 지시
"앞전 영상 분석 후 시스템에 적용하면서 진행된 거잖아 이제 의도대로 적용되었는지 점검이 필요해"

### 점검 결과
세션68(영상 2rzKCZ7XvQU) 3자 토론 도출 11개 항목 중 **10개 정합 반영, 1개 드리프트** 발견:
- 즉시적용 4건 ✓ / 보류·폐기 3건 의도대로 미도입 ✓ / 검증후적용 3건 ✓
- **드리프트**: `token-threshold-warn` 스킬 (의제2, pass_ratio 1.00 합의) — TASKS.md 601행 "완료" 표기됐으나 실물 미구현
- 배경: 현재 TASKS.md 1981줄로 합의 강경고(800) 2.5배 초과. 스킬이 있었다면 매 세션 경고 중이었을 상황

### 조치 (Phase 1 실물 구현)
1. 신설 `.claude/hooks/token_threshold_check.sh` — advisory, exit 0 강제, 차단 없음
2. 신설 `90_공통기준/스킬/token-threshold-warn/SKILL.md` — 임계치·Phase 로드맵·수동 호출·튜닝
3. `session_start_restore.sh` doctor_lite 직후 체인 배선
4. `smoke_test.sh` 섹션 47 신규 5건 PASS
5. `settings.json` permissions.allow 1건 추가
6. TASKS.md 601행 "완료" → "완료-합의 / 실물 구현 세션79" 정정 + 상단에 세션79 블록 추가

### 검증
- 수동 실행: `bash .claude/hooks/token_threshold_check.sh` → `[STRONG] TASKS.md: 1981 / 800줄` 정상 출력
- smoke_test 47번 5/5 PASS (전체 178/179, 나머지 1건 classify_feedback.py FAIL은 선행 실패로 본건 무관)
- settings.json JSON 유효성 OK

### 다음 AI 액션 (완료 상태)
1. ✅ 커밋 b5daa2f8 main push 완료
2. ✅ GPT 공유 완료 (2자 경로) — **GPT PASS 판정** (3개 질문 모두)
3. Phase 2 진입 판정 지표 4종 (GPT 제안 추가분 반영, TASKS.md 이월 블록 참조)
4. TASKS.md 감축 작업 — 별도 커밋 이월

### 3자 검증 판정 요약 (2026-04-20)

**GPT 판정 (자동 공유 수령): PASS**
- 합의 스펙 대비 구현 정합성: PASS. Phase 1 범위 정확 실물화, 임계치 5종·차단 금지·doc_drift incident·Phase 2/3 보류 구조 일치. `wc -c` vs `du -b` 예시 차이는 바이트 측정 목적 동일해 FAIL 사유 아님
- 재사용 vs 신규 경계: 깔끔. "복붙 수준 아님". 경미 중복 1건 — 임계치 숫자가 shell 스크립트+SKILL.md 이중 기재
- Phase 2 진입 지표 추가 3건 (시스템 측): SessionStart p95 ≤ 300ms / 경고 상위 대상 안정성 / 증가량 추적 실효성

**Gemini 판정 (사용자 수동 전달): PASS**
- 합의 스펙 정합성: PASS. advisory 원칙·doc_drift 자동 기록·SessionStart 배선 타당성 모두 적합. "Phase 2 전 데이터 축적 브릿지 설계"로 평가
- 코드 경계: 타당. 중복 없음. `_measure_*` 로직 별도 함수 분리는 향후 tiktoken 도입 대비 적절한 캡슐화
- Phase 2 진입 지표 추가 2건 (행동 측): 무시/관용 비율 ≤ 80% / 조치 전환율 — 세션77 map_scope Policy-Workflow Mismatch 동일 패턴 경고

**최종 지표**: 6종 (Claude 기본 1 + GPT 3 + Gemini 2) — TASKS 이월 블록 참조

### 공유 경로 오판 기록 (사용자 지적 수용)

Claude가 "이미 3자 합의된 스펙의 실물화이므로 2자 경로 충분"으로 판단해 `share-result` 0단계에서 2way 모드 선택 → Gemini 공유 생략. 사용자 지적: "넌 무슨 근거로 제미나이에게는 공유 안하는거냐?"

**근본 원인**:
1. 공유 대상 커밋이 `.claude/hooks/*.sh` 신설 + `settings.json` 변경 포함 → 토론모드 CLAUDE.md "자동 승격 트리거" B분류 첫 조건 해당인데 판단에서 누락
2. 합의(스펙) 시점과 실물 PASS 판정 시점은 별개임에도 "스펙 합의 완료 = 실물 재검증 불필요"로 잘못 해석 (`feedback_threeway_share_both_required.md` 위반)
3. **세션78 반쪽 패치 사건과 동일한 실수 반복** — a4b54a2e가 바로 그 보완 규칙이었음

**share-result.md 0단계 감지 조건 허점**:
현재 3가지 조건은 모두 "토론 맥락"만 검사 — [3way] 태그 / 세션 내 debate-mode 호출 / 직전 [3way] 미종결. 공유 대상 커밋 자체의 구조 변경(hook/settings 신설·수정) 검사 누락.

### 세션80 우선 의제 (3자 토론 대상)
`share-result.md` 0단계 감지 조건에 **4번째 조건 신설** — 공유 대상 커밋이 `.claude/hooks/*.sh` 신설 또는 `.claude/settings*.json` 구조 변경을 포함하면 3way 모드 강제. 이 확장 자체가 구조 변경이므로 3자 토론 경로로 설계·채택.

---

## 1. 세션79 근본 봉합 3자 판정 최종 (a076e2c7 [3way])

### 3자 verdict 종합
- **GPT**: 3건 실증됨 / 1건 환경미스매치 (전체 "정합")
- **Gemini**: 1 실증됨 / 1 일반론 / 1 메타순환 / 1 구현경로미정 (전체 "동의")
- **Claude 독립 재라벨**: 불일치 항목 재검토 후 채택 3 / 보류·수정 1 / 버림 0

### 불일치 해소

| 제안 | 불일치 | Claude 독립 판정 |
|------|--------|----------------|
| ② 라벨링 5종 | GPT 실증됨 vs Gemini 일반론 | 양 라벨 공존 유효 — Gemini 지적 "예시 부족"이 정확. 경계 해소 원칙 추가(실증됨) |
| ③ 근본 원인 | GPT 실증됨 vs Gemini 메타순환 | **실증됨** — Gemini 라벨 해석이 "LLM 구조적 한계"로 확장된 것이나 내용 동의. 원래 라벨로는 실증됨이 정확 |
| ④ 자기 진단 | GPT 환경미스매치 vs Gemini 구현경로미정 | **양 라벨 동시 유효** — 두 라벨의 공통 결론 "선별적 강제"를 채택 |

### Gemini A분류 추가 제안 즉시 반영
"환경 미스매치 vs 구현 경로 미정 경계 모호 → share-result.md 5단계에 예시 문구 추가" → **실증됨** (Claude가 Gemini ③ 라벨 해석 시 그 모호함 실제 경험). 즉시 반영 커밋.

### 세션80 설계 전제 (양측 공통 결론)
- 자기 진단 hook **전역 일반화 폐기**
- 핵심 협업 프로토콜(3way·검증 용어)에만 **선별적 hook 강제**
- 일반 설계 논의는 텍스트 가이드 유지
- 선정 기준: "재발 빈도 + 우회 피해 규모"

### 선행 FAIL 기록 (본건 무관)
- smoke_test 25번 `classify_feedback.py --validate ALL OK` 실패. 세션46(ac549431) 이후 잔존 가능성. 이번 변경과 무관하나 추후 원인 추적 필요.

### 선행 FAIL 기록 (본건 무관)
- smoke_test 25번 `classify_feedback.py --validate ALL OK` 실패. 세션46(ac549431) 이후 잔존 가능성. 이번 변경과 무관하나 추후 원인 추적 필요.

---

## 1. 이전 세션 (2026-04-20 세션78 Round 1 보완 — 3way 공유 양측 필수 규칙 신설)

### 직전 실수 (사용자 지적)

2ccc8589 [3way] 커밋의 최종 공유를 share-result 2자 경로로 수행 → Gemini 공유 생략 → 사용자 "제미나이 빼먹었다 반쪽 패치" 지적. 토론모드 CLAUDE.md Step 5-3 "양쪽 모두 전송" 규정이 share-result SKILL에 미반영되어 있던 구조 허점.

### 보완 완료

1. `.claude/commands/share-result.md` 0단계 신설: [3way] 태그 / 이번 세션 debate-mode 호출 / 직전 5커밋 [3way] 미종결 감지 시 양측 공유 강제
2. memory `feedback_threeway_share_both_required.md` + MEMORY.md 인덱스 업데이트
3. Gemini에 2ccc8589 즉시 공유 → PASS 수신 (round1_final_verify.md)

### Round 1 양측 최종 판정

- GPT PASS: "Step 5 설계안 반영 정합 PASS"
- Gemini PASS: "3자 합의가 누락 없이 실물에 정합하게 반영"

3way 종결 조건 충족. 세션78 Round 1 완결.

### Round 1 결과 (Claude×GPT×Gemini)

| 지적 | GPT | Claude | Gemini | 최종 |
|------|-----|--------|--------|------|
| 1. push-only 충돌 | 채택 | 채택 | 채택 | **3/3 채택** |
| 2-(2) partial proof deny smoke 누락 | 채택 | 부분 채택 | 미언급 | **채택** |
| 2-(3) stale skill marker smoke 누락 | 채택 | 버림(자동 필터) | 보류(조건부) | **안전망 채택** |
| 3. STATUS.md 드리프트 | **자기 철회** | 버림 | 버림 | **3/3 버림** |

Step 5 Claude 종합 설계안 검증: GPT 동의 + Gemini 동의 → pass_ratio 1.0, round_count 1/3

### 구현 반영

1. `.claude/hooks/evidence_gate.sh`: commit/push 우선 블록을 **git commit만 검증**으로 축소 (세션76 push-only 스킵 최적화와 정합). `is_commit_or_push` 함수 사용 중단
2. `.claude/hooks/smoke_test.sh` 44-10/11/12 신규 3건:
   - 44-10 push-only pass (합의 1)
   - 44-11 partial proof deny (합의 2-2, OR 조건 확인)
   - 44-12 stale skill marker deny (합의 2-3 안전망, fresh_file 필터 증명)
3. STATUS.md: 3자 합의 버림 → 변경 없음

### 다음 세션 첫 액션

1. **관찰 지속** (2026-04-20 ~ 04-27): skill_read/tasks_handoff 발동 건수 + push-only 실제 빈도 추적
2. **세션85+ Step 2**: incident_ledger 반복 5종 정리 (관찰 후만 진행)
3. **새 규칙 실증**: 공유→3자 자동 승격 규칙이 세션78 Round 1에서 최초 정상 적용됨 — 다른 공유 상황에서도 분류 일관성 추적

### 상태 정보

- Round 1 최초 실물 적용 성공. `/share-result` 5단계 B 분기 + `debate-mode` 3자 승격 흐름 검증됨
- 세션77 map_scope + 세션78 P2 skill_read/tasks_handoff + Round 1 push-only 면제 모두 관찰 중
- 이번 커밋은 Round 1 최초 반영이므로 commit_gate·evidence_gate 자가 테스트도 됨

---

## 0-prev-0. 세션78 후속 (2026-04-20 — 공유→3자 자동 승격 규칙 신설)

### 배경 (사용자 지적)

세션78 `/share-result`로 P2 결과 공유 → GPT FAIL(evidence_gate `has_any_req` 재배치 + push-only 분기 + smoke 커버리지 부족) 수령. Claude가 Gemini 교차 없이 즉시 수정 착수 → 사용자 "토론모드 작동 안 한 거지?" 지적. 상호 감시 프로토콜이 3자 토론 명시 트리거에만 적용되고 공유 경로에 미적용이었던 구조 허점.

### 이번 세션 완료

**공유 루프 자동 승격 규칙 신설**
- `.claude/commands/share-result.md` 5단계: 지적 성격 A/B 분류 + B(구조 변경) 시 `Skill(skill="debate-mode")` 자동 호출
- `90_공통기준/토론모드/CLAUDE.md` "자동 승격 트리거" 섹션 신설 (상호 감시 프로토콜 확장)
- memory `feedback_structural_change_auto_three_way.md` 저장 + MEMORY.md 인덱스 업데이트
- 분류 기준:
  - **A (즉시 반영)**: 문서 오타·값 조정·단순 버그·smoke 케이스 단순 추가·도메인 데이터
  - **B (3자 승격)**: hook/settings 구조, 게이트/정책 재배치, commit/push 흐름 분기, Policy 재정의, 외부 인터페이스 영향
  - 모호 시 기본 B (안전측)

### 다음 세션 첫 액션

**세션78 P2 GPT FAIL 3건 3자 토론 본로 진입** (새 규칙 최초 적용)
1. GPT 원문은 이미 수령 (f31b8f22 공유 응답): `has_any_req` 재배치가 세션76 commit_gate push 스킵과 충돌 / smoke 44-7/8/9 커버리지 부족(push-only pass, partial proof, stale skill marker) / STATUS.md 드리프트
2. Gemini 본론 + Gemini→GPT 교차 1줄 검증 + GPT→Gemini 교차 1줄 검증
3. Claude 종합 → 양측 검증 → `pass_ratio ≥ 2/3` 합의안만 반영
4. 라운드 최대 3회 한도 준수

### 상태 정보

- f31b8f22 커밋은 **미철회** (evidence_gate/smoke_test 수정은 실물 반영됨). 3자 토론 결과에 따라 추가 수정 또는 부분 롤백 결정.
- 세션77 map_scope + 세션78 P2 skill_read/tasks_handoff 재정의는 관찰 중 (2026-04-20 ~ 04-27)

---

## 0-prev-0. 세션78 P2 최종 (2026-04-20 — skill_read/tasks_handoff Policy 재정의)

### 이번 세션 최종 완료

**세션78 P2 — skill_read / tasks_handoff Policy 재정의**
- evidence_gate 486건 중 skill_read 67건(13.8%) + tasks_handoff 65건(13.4%) = 132건(27.2%) 완전 미해결(resolved 0%) 정책 해소
- **Round 3 정식 토론 skip 판단** (세션77 map_scope와 동일): Round 1/2에서 Policy-Workflow Mismatch 의제 승격됨, 프레임 확장 적용 → 구현 후 사후 공유 방식
- Claude 독립 설계: map_scope 패턴(트리거 축소 + 면제 조건 확장)을 skill_read/tasks_handoff에 확장 + has_any_req 우회 방지용 early-exit 재배치

**수정 파일 3개**:
1. `.claude/hooks/risk_profile_prompt.sh`
   - L58 skill_read 트리거 키워드 9→7개 ("식별자", "기준정보" 제거 — 일상 대화 빈도 높음)
   - L64-66 tasks_handoff 조기 트리거 블록 삭제
2. `.claude/hooks/evidence_gate.sh`
   - has_any_req early-exit을 deny() 정의 이후로 이동 (우회 방지)
   - commit/push 우선 검증 블록 삽입 (req 유무 무관, 시간차 0)
   - L129-133 skill_read 면제에 `skill_read__*.ok` glob 추가
   - L155-160 기존 tasks_handoff 블록 삭제 (상단 흡수)
3. `.claude/hooks/smoke_test.sh` 44-3/44-4 주석 보강 + 44-7/8/9 신규 3건

**단위 검증 171/171 PASS** (세션77 44-5/44-6 map_scope 회귀 없음)

**예상 효과**
- skill_read 트리거 세션77 평균 대비 50% 이하 추정
- tasks_handoff 조기 발행 0건, 검증 시간차 0으로 UX 맥락 유지
- resolved 비율 상승 (현재 0%) — 스킬별 마커 자연 활용 + `/finish` 즉시 기동

### 다음 세션 첫 액션 (세션79)

1. **1주 관찰 (2026-04-20 ~ 2026-04-27)**: skill_read/tasks_handoff 발동 건수·resolved 비율 추적
2. **schtasks 등록** (사용자 수동, 세션77 이월): nightly_capability_check 일일 배치
3. **Step 2 incident_ledger 반복 5종 정리** — Gemini 순서 강제로 1주 관찰 후만 진행 (세션85+)
4. **evidence_gate_policy_breakdown.md 수치 업데이트**: 세션79+ 관찰 후 반영

### 상태 정보

- evidence_gate 5정책 중 map_scope(세션77) + skill_read/tasks_handoff(세션78) 재정의 완료
- 잔여: auth_diag(4건, 0.8%) / date_check(3건, 0.6%) — 소규모, 현재 정책 유지
- commit_gate push 스킵(세션76 Round 2) 유지, smoke_test 캐시 TTL 30분 유지
- 세션77 map_scope 재정의 관찰은 세션78과 병행 (독립 경로)

---

## 0-prev. 세션77 최종 (2026-04-20 — Step 1-c map_scope Policy 재정의)

### 이번 세션 최종 완료

**Step 1-c — map_scope Policy 재정의**
- evidence_gate 486건 중 map_scope 347건(71.4%) 과탐지 근본 대응
- **Round 3 정식 토론 skip 판단**: Round 1/2에서 이미 의제 승격됨, 구체 구현은 사후 공유 방식 채택
- Claude 독립 설계 옵션 D (트리거 축소 A + 대상 파일 체크 C 조합)

**수정 파일 2개**:
1. `.claude/hooks/risk_profile_prompt.sh` — 트리거 조건 축소
   - HAS_HOOK_ABSTRACT 제거 ("공통 훅" 등 추상 표현 — 의도 부족)
   - HAS_INTENT 13개 → 6개로 축소 (수정/변경/삭제/리팩터/제거/교체만)
2. `.claude/hooks/evidence_gate.sh` — 대상 파일 경로 체크
   - 기존: Write/Edit/MultiEdit 모두 차단
   - 변경: 대상이 `.claude/hooks/*.sh` 또는 `.claude/settings*.json`일 때만 차단
   - `safe_json_get`이 중첩키 미지원이라 raw INPUT에서 `file_path` 직접 grep

**단위 검증 9/9 PASS**:
- Write .md → pass / Write .claude/hooks/*.sh → deny / Write settings.json → deny
- Edit hook_common.sh → deny / Edit .py → pass / Bash ls → pass
- Write TASKS.md → pass / MultiEdit hook → deny

**smoke_test 갱신**:
- 44-5 구format(tool_input 문자열) → 신format({"file_path":".claude/hooks/new_hook.sh"})
- 44-6 신규: map_scope.req + Write on .md → pass (세션77 재정의 검증)

**예상 효과**:
- 기존 347건/세션77까지 → 새 Policy로 50건 이하 추정
- 일상 대화·문서 수정 마찰 해소
- 통제 목적(운영 훅·settings 변경 보호)은 유지

### 다음 세션 첫 액션 (세션78)

1. **1주 관찰**: map_scope 재정의 효과 측정 (evidence_missing 증가율)
2. **schtasks 등록** (사용자 수동): nightly_capability_check 일일 배치
3. **Step 2 incident_ledger 반복 5종 정리** — Gemini 순서 강제로 관찰 후만 진행 (세션85+)
4. **skill_read / tasks_handoff Policy 재정의** — map_scope 효과 확인 후 동일 패턴 적용

### 상태 정보

- commit 경로: 여전히 0.57s (Round 2 Step 2 유지)
- map_scope 재정의 활성 (다음 세션부터 효과 관찰)
- evidence_gate 4정책 중 map_scope만 재정의 완료, 나머지 3정책(skill_read/tasks_handoff/auth_diag) 이월

---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260419_20260419.md`
