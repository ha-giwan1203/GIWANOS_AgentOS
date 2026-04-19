# evidence_gate 정책별 분해 (Round 1 Step 1-b 완료)

> 세션77 Round 1 Step 1-b 수행. 전수 486건을 5정책으로 분해 실증. Step 1-c Policy 재정의 입력 근거.

## 배경

- 세션75 Round 1 Step 1-a에서 최근 100건을 분석하여 3정책(map_scope/skill_read+identifier_ref/tasks_handoff) 존재 확인
- 본 Step 1-b에서 **전수 486건을 5정책으로 분해**하여 실제 비율 확정
- `.claude/docs/evidence_gate_policy_breakdown.json`에 JSON으로 저장

## 결과

### 정책별 분포 (486건 전수)

| 정책 | Count | % | Unresolved | Resolved |
|------|-------|---|------------|----------|
| **map_scope.req** | **347** | **71.4%** | 246 | **101** |
| skill_read.req / identifier_ref.req | 67 | 13.8% | 67 | 0 |
| tasks_handoff.req | 65 | 13.4% | 65 | 0 |
| auth_diag.req | 4 | 0.8% | 4 | 0 |
| date_check.req | 3 | 0.6% | 2 | 1 |
| **합계** | **486** | **100%** | 384 | 102 |

### 핵심 인사이트

#### 1. map_scope.req 단일 정책이 71.4% 압도적 점유
- Round 1 추정(46.2%)보다 훨씬 큰 비중
- **Step 1-c Policy 재정의 시 map_scope 단일 재설계만으로 incident 70% 감소 가능**
- 해결된 101건도 전부 map_scope → 이 정책이 "해결 가능한" 유일한 정책임을 시사

#### 2. skill_read + tasks_handoff = 132건 (27.2%) 전부 미해결
- 둘 다 resolved=0
- 정책 기준이 실무 워크플로우와 mismatch로 사용자가 해소 시도조차 하지 않는 상태
- Gemini Round 1 지적 "false_positive_suspect" 정확히 일치

#### 3. auth_diag.req·date_check.req 소규모(≤4)
- 총 7건. 재정의 우선순위 낮음
- 유지 시 incident 영향 미미

## Policy 재정의 우선순위 (Step 1-c 입력)

| 순위 | 정책 | 대상 | 근거 |
|------|------|------|------|
| **1 (최우선)** | **map_scope.req** | 347건 | 단일 정책 재정의로 incident 70% 감소. "고위험" 기준 명확화 필요 |
| 2 | skill_read.req | 67건 | SKILL.md 미읽기 엄격 정책 완화 검토 (현재 0% resolved) |
| 2 | tasks_handoff.req | 65건 | commit 직전 자연 흐름 고려한 trigger 시점 재설계 |
| 3 | auth_diag.req / date_check.req | 7건 | 규모 작아 유지 권장 |

## map_scope.req 심화 분석 — 가장 큰 Leverage

### detail 정규화
> "map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언(map_scope.ok) 없이 고위험 수정 금지."

### 문제 패턴
- "고위험 수정"의 판정 기준이 broad하여 **거의 모든 수정이 map_scope.ok 증적 요구 대상**
- 현재 resolved 101 vs unresolved 246 → 약 29% 해결률 (다른 정책 0% 대비 양호하지만 여전히 저조)
- **Round 1 최근 100건 분석에서는 resolved 0건** → 최근일수록 사용자가 정책 준수 시도 포기 경향

### Step 1-c 재정의 방향 후보

**옵션 A**: "고위험" 기준을 축소
- 현재: 모든 파일 수정 대상
- 개선: 수치/수식/참조구조 변경 + 실무 파일만 (data-and-files.md Full Lane 기준 차용)
- 예상 효과: map_scope 요구 70% 감소 → 347 * 0.3 = 104건으로 감축

**옵션 B**: map_scope.ok 증적 자동 생성
- 사용자가 3줄 선언을 쓰지 않아도 Claude가 자동 작성 후 사용자 승인
- Claude 도구 호출 직전 자동 프롬프트
- 예상 효과: resolved 비율 29% → 90%+

**옵션 C**: map_scope 완전 폐지 후 skill-level 가이드
- "고위험 수정 전 /map-scope 호출" 을 훅 강제가 아닌 skill 내부 체크리스트로 전환
- 예상 효과: incident 0건 but 통제력 완전 상실 리스크

**Claude 권장**: 옵션 A + B 조합
- A로 "고위험" 정의 명확화
- B로 잔존 요구는 자동 생성
- C는 위험 (통제 상실)

### skill_read.req / tasks_handoff.req 재정의

**skill_read.req (67건, 0% resolved)**:
- 현재: SKILL.md 읽기 전 모든 스킬 실행 금지
- 개선: 1회 읽으면 해당 세션 내 동일 스킬 재호출 허용 (현재 매 호출마다 재검증)
- 예상 효과: 67건 → 15건 (session 단위 캐시)

**tasks_handoff.req (65건, 0% resolved)**:
- 현재: TASKS/HANDOFF 갱신 없이 commit/push 금지
- 개선: commit 직전 자동 trigger (작업 시작 시점 아닌)
- 예상 효과: 65건 → 5건 (자연 흐름 정합)

## 세션78 이월 — Step 1-c Policy 재정의 실행

1. map_scope.req 재정의 (옵션 A + B) 초안 작성
2. 세션78 시작 시 3자 토론 Round 3 개시 (Gemini Policy-Workflow Mismatch 종합 감사 의제)
3. skill_read·tasks_handoff 재정의는 map_scope 검증 후 순차

## 측정 근거

- `.claude/incident_ledger.jsonl` 기준 2026-04-19 14:47 KST 집계
- 파일 전체 1027건 중 evidence_gate 486건
- Python 3.12 json.loads + Counter 집계

## 연관 문서

- Round 1 Step 1-a: `.claude/docs/incident_labeling_protocol.md` + `incident_labels_evidence_gate_100.json`
- Round 1 로그: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/`
- Round 2 로그: 같은 폴더 round2_*.md

## 결론

**Step 1-b 완료. map_scope.req 71.4% 단일 정책이 Step 1-c 재정의 최우선 타겟 확정.**
다음 세션에서 Gemini 경고("evidence_gate 474건 Policy 재설계 필요")에 대한 구체 실행안 착수.
