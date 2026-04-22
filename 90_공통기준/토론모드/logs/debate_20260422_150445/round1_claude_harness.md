# Round 1 — Claude 하네스 분석 + 독립 의견

## 하네스 분해 (summary_counts: 채택 5 / 보류 2 / 버림 0)

### 채택
1. **evidence 축 "coverage 축소 우선"** — 라벨: 실증됨
   근거: [risk_profile_prompt.sh:75-85](.claude/hooks/risk_profile_prompt.sh) 주석에 세션77·78 "HAS_INTENT 13→6개 축소" 이력. 축소 방향이 옳다는 건 자기증명. 채택.
2. **hook_registry 폐기 후 list_active_hooks 흡수** — 라벨: 실증됨
   근거: `hook_registry.sh check` 실제 실행 시 31/31 중 29건 WARN. 고치기보다 폐기 후 기준축 이전이 합리. 채택.
3. **selfcheck 24h 정확 집계** — 라벨: 실증됨
   근거: [selfcheck.sh:75-77](.claude/self/selfcheck.sh) CUTOFF="%Y-%m-%dT%H" grep prefix. 채택.
4. **doctor_lite 환경 의존 축소** — 라벨: 실증됨
   근거: [doctor_lite.sh:15](.claude/hooks/doctor_lite.sh) python3 하드의존 vs [smoke_fast.sh:33](.claude/hooks/smoke_fast.sh) fallback 비대칭. 채택.
5. **state_rebind_check detect-only 전환** — 라벨: 실증됨
   근거: README 상 advisory·detect-only 등급이지만 [state_rebind_check.sh:30-53](.claude/hooks/state_rebind_check.sh) 실제로는 TASKS 12줄+HANDOFF 20줄 content injection. 등급과 실동작 불일치. 채택.

### 보류
6. **"남기는 evidence 3종 = date_check / auth_diag / identifier_ref"** — 라벨: 구현경로미정
   근거: [evidence_mark_read.sh:34-105](.claude/hooks/evidence_mark_read.sh) 현재 마커 15종 이상(skill_read, domain_read, tasks_read, handoff_read, status_read, debate_entry_read, debate_claude_read, tasks_updated, handoff_updated, domain_X__Y.ok 등). harness_gate·debate_gate·instruction_read_gate·skill_instruction_gate 등이 각각 고유 마커에 의존. 3종 축소의 실제 폐기 범위·대체 경로 없이 선언만 하면 연쇄 실패. 다음 라운드에서 "현재 마커 15종 × 의존 게이트 매핑 표" 필요.
7. **"gate_boundary_check → lint 유지, 실제 보증은 smoke 시나리오"** — 라벨: 구현경로미정
   근거: smoke_fast(11건)와 smoke_test(105건)는 이미 존재. GPT 제안의 "경계 시나리오"가 smoke_test 중 무엇을 의미하는지, 신규 추가인지 기존 케이스 라벨 재분류인지 명확하지 않음. 다음 라운드에서 구체 시나리오 카탈로그 필요.

### 버림
없음.

## Claude 독립 의견 (GPT 초안에 추가 보완)

### (가) 세션86 실측 자료를 계획 검증 지표로 승격
GPT 초안은 "incident 감소율" 정성 평가만 있음. 세션86 실측(7일 272건 미해결 / 120~300 구간 82~93% 초과)이 이미 있으므로:
- **정량 목표**: coverage 축소 후 **evidence_gate 7일 미해결 건수 50% 이하** (272→136건 이내)
- **관찰 기간**: 1주차 반영 완료 후 7일 관찰 → 미달성 시 contract형 재설계(5번) 재검토

### (나) 7단계 순서의 비용 구분
1~3번(hook_registry/selfcheck/doctor_lite)은 각각 **수십분~1시간 단위 수정**. 계측 정비 단계.
4번(evidence coverage 축소)은 **하루~며칠 단위 수술**. 본 수술.
5번(contract형 재설계)은 **별도 의제 승격** 권고 — 1주차에 묶지 말고 1주차 실측 데이터 수령 후 2주차 초에 재판단.

### (다) 1주차/2주차 경계 재정의
GPT 제안은 1주차=1~4 / 2주차=5~7 암묵. Claude 제안:
- **1주차 = 1~3 + 4 착수**: 계측 정비 + evidence 축 coverage 축소 1차 (map_scope·tasks_handoff 관련 broad req 제거)
- **2주차 = 5 + 6 + 7**: 남긴 3종 contract형 재설계 + state 경량화 + boundary 시나리오 테스트
- **이유**: 4번이 1주차 뒷부분에 들어가야 2주차 5~6~7이 4번 결과를 전제로 설계 가능

### (라) 사용자 지시 "전체 시스템 구조 관점"에 대한 Claude 추가 관찰
GPT 초안이 축 단위 구조 관점은 충족. Claude 추가 관찰 한 가지:
**evidence 축과 진단 축은 실은 같은 뿌리** — "Claude가 무엇을 읽었는가"를 grep으로 추론하는 동일 패턴을 공유. evidence_mark_read가 문서 읽기 추론, selfcheck 24h가 incident 시간 추론, gate_boundary_check가 의미 위반 추론. 세 훅 모두 "정확한 이벤트 소스 없이 사후 텍스트로 근사"하는 구조. 4번+7번을 별도 수술로 두지 말고 "grep 기반 근사 → 이벤트 기반 계약"의 **단일 구조 전환**으로 묶는 관점도 검토 대상.

## 다음 라운드 입력안
1. 보류 2건 해소: (a) 마커 15종 × 의존 게이트 매핑, (b) smoke_test 경계 시나리오 카탈로그
2. 실행계획 문서 압축 수락: 1주차/2주차 (Claude 경계 재정의안 기준) + 검증 기준(세션86 실측 지표 승격) + 롤백 조건
3. (라) 단일 구조 전환 관점 GPT 판단 요청
