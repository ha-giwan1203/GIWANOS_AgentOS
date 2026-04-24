# Round 1 — Claude 종합

> 사용자 새 지침(2026-04-24) "시스템 개선 시 전체 구조 영향 분석 필수" 적용 — 종합 단계에서 4단계 회귀 체크 명시.

## 1. 양측 답변 집계

| 항목 | Claude 사전 | GPT | Gemini | 합의 |
|------|-----------|-----|--------|------|
| Q1 protected_assets 위치 | A | A | A | **3/3 A안** |
| Q2 README Failure Contract | B | B | B | **3/3 B안** |
| Q3 hook_common wrapper | A | A | C | 2/3 A안 |
| Q4 커밋 묶음 vs 분리 | A | B | A | 2/3 A안 → **B안 재검토** |

## 2. 사용자 지침 반영 4단계 시스템 영향 분석

### 1) 의존성·참조 체인
- `auto_commit_state.sh` ← `settings.json:339-380` Stop hook 5번째 등록
- `auto_commit_state.sh` → `final_check.sh --fast` (직전 호출, 세션101 d47f0515)
- `protected_assets.yaml` ← `protect_files.sh` 검사
- `README.md` Failure Contract 섹션 ← `render_hooks_readme.sh`는 **숫자만 자동 갱신**, 표 본문은 수동 편집 (확인 완료 — render 스크립트 충돌 없음)

### 2) 동일 패턴 사용처
- 다른 advisory hook 6종 (skill_drift_check, permissions_sanity, doctor_lite 등) — 모두 README Failure Contract 등재
- hook_common wrapper 사용처: `hook_advisory` / `hook_gate` / `hook_measure` 분기

### 3) 호출 순서·등급·실행 흐름 영향
- Stop 순서 불변 (Q3 A안)
- `hook_advisory` 래핑 = exit 0 강제 → 실행 흐름 변경 없음 (timing/incident만 추가)
- protected_assets 등록 = protect_files 차단 추가 (의도된 동작, 회귀 아님)

### 4) 회귀 시나리오
- **R1**: protected_assets 추가 → 사용자 직접 수정 시 차단 = 의도된 보호
- **R2**: README 표 추가 → render 스크립트 충돌 없음 (숫자만 자동)
- **R3**: hook_advisory 적용 → 매 Stop마다 timing 기록 = log size 미세 증가 (영향 낮음)
- **R4**: 분리 커밋 → 첫 커밋 후 두 번째 커밋 전 final_check FAIL 가능성 = 첫 커밋이 wrapper 미적용이므로 기존 동작 유지 (안전)

## 3. Q3·Q4 의견 차이 분석

### Q3 (hook_advisory vs hook_gate)
- **Gemini C안 (hook_gate)**: "final_check FAIL은 명백한 게이트 사유 → exit 2로 명시적 중단"
- **Claude/GPT A안 (hook_advisory)**: "Stop hook advisory 등급 유지, push 차단은 이미 보장됨"
- **차이**: hook_gate(C안)는 Stop 전체를 exit 2로 중단 = 등급 체계 변경 (B 분류 구조 변경)
- **결론**: A안 채택. Gemini C안은 "Stop hook 등급 변경" 별도 의제로 분리 (B 분류 자동 승격 대상)

### Q4 (단일 vs 분리 커밋)
- **Claude/Gemini A안**: "단일 목적 = 단일 커밋 = 원자성"
- **GPT B안**: "계약 문서 vs 실행 파일은 회귀 추적 단위가 다르다"
- **사용자 새 지침 반영**: "한 곳 수정이 다른 곳을 무너뜨림" → wrapper 적용은 실행 파일 변경이라 회귀 위험 더 큼
- **결론**: B안 채택. Claude 입장 변경. 분리 커밋으로 git bisect 추적 단위 명확화

## 4. 최종 종합안

| 항목 | 채택 |
|------|------|
| Q1 | **A안** — 기존 Stop 블록에 추가 |
| Q2 | **B안** — incident 기록 + 자동 push 차단 |
| Q3 | **A안** — hook_advisory 래핑 (Gemini C안은 별도 의제로 이월) |
| Q4 | **B안** — 분리 커밋 (Claude 입장 변경, 사용자 지침 반영) |

## 5. 실행 계획

**커밋 1** [3way]: P-1 + P-2 = 문서 계약 보강
- `90_공통기준/protected_assets.yaml` Stop 블록에 `auto_commit_state.sh` 추가
- `.claude/hooks/README.md` Failure Contract 표에 advisory + final_check FAIL 시 incident 기록 + 자동 push 차단 추가

**커밋 2** [3way]: hook_common wrapper 적용 = 실행 파일 변경
- `.claude/hooks/auto_commit_state.sh`에 `source hook_common.sh` + `hook_advisory` 래핑

**Round 2 검증**: 양측에 종합안 1줄 검증 요청 (동의/이의/검증 필요)

**이월**: Gemini Q3 C안 (hook_gate 격상) — 별도 의제 "Stop hook 등급 체계 재검토"
