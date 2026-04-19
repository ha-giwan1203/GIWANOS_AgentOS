# Round 2 — GPT 답변 (의제: smoke_test 3분 병목 최적화)

## Round 2 의제
세션75 Round 1 "Policy-Workflow Mismatch" 의제의 2호 구체 사례로 smoke_test.sh 병목 분석 + 해결.

## 상황 실측
- bash smoke_test.sh: real 3m20s / user 1m16s / sys 1m47s / 167/167 PASS
- final_check --full의 92% 점유
- 외부 호출: bash -n 20회, grep 123회, python3 5회

## GPT 1차 응답 (판정 + 방안 3개)

**판정**: Windows Git Bash/MSYS2 subprocess 오버헤드가 주원인 — 프로세스 생성·경로변환·파일 I/O 비용이 sys 54%로 터진 형태.

**근본 최적화 방안 3개**:

**A. 파일별 단일 스캔 러너로 재구성**
- 효과: 가장 큼. hook_common.sh 등을 수십 번 grep하지 말고 1회 읽어 다중 규칙 검사. awk 1회 또는 Python 1회 러너.
- 공수: 중~상. check() 구조 유지 + 검사 함수만 집약.

**B. regression/capability + 파일 의존성 기준 분할**
- 효과: 큼. commit 경로 regression만, capability는 --full-deep 또는 수동.
- 공수: 중. 실행 정책만 변경.

**C. 섹션별/의존파일별 해시 캐시 + 의존성 맵**
- 효과: 큼. hook_common.sh만 바뀌면 관련 섹션만, navigate_gate.sh면 45번대만 재실행. TTL보다 정확.
- 공수: 중.

**Claude TTL 30분 캐시 평가**: 안전망으로만 유지, 주 판정은 섹션별 입력 해시로 교체 권장.

**세분화 방향 타당성**:
- a) hook별 해시 캐시: 가장 타당. 정확히는 섹션별/의존파일별 해시 캐시. 43-44는 hook_common + evidence 공용 물고 있음.
- b) 병렬 실행 (xargs -P / GNU parallel): **보류** (MSYS2 안티패턴, 프로세스 폭증·경합).
- c) grep/sed 통합: 타당. 저공수·큰 효과.

**추가 제안**:
- smoke_test는 "정책 검증 vs 구문/존재 검증" 분리 필요
- 우선순위: (1) 외부 호출 통합 → (2) 섹션별 해시 캐시 → (3) commit 경로에서 capability 제외

## GPT 2차 응답 (Gemini 이의에 대한 입장 재정립)

**판정**: 동의 (A안 최우선 자진 철회)
- 원인 진단·병렬화 보류는 맞고, A안 최우선은 과했음
- **Gemini 재배치 수용** — 병목이 "설계 재작성" 문제 아니라 "무엇을 언제 돌릴지" 문제
- **Test Pruning 수용** — 167케이스 → 3분류: (a) 커밋 필수 회귀 (b) full 전용 구조 검증 (c) 중복/저가치
- **블랙박스화 비판 부분 수용** — A안 최후순위 유지, 단 "섹션별 보조 러너 + PASS/FAIL 형식 유지" 조건이면 블랙박스화 줄일 수 있음

**GPT 최종 권장 순서**:
1. Test Pruning
2. regression/capability 분할
3. 섹션별/의존파일별 해시 캐시
4. grep/sed 중복 통합
5. 필요 시에만 A안 (부분 재구성)

## GPT Round 2 최종 검증 (Claude 종합 설계안 대상)

**판정: 동의**
- final_check --full에서 smoke_test.sh가 직접 병목
- smoke_test.sh 내부에 이미 regression/capability 라벨이 있어 재작성보다 pruning·실행 분할·정밀 캐시를 먼저 거는 순서가 실물과 가장 잘 맞음

**수정 제안 1점**:
- Step 1 (c) "중복/저가치 삭제" → **"격리 후보로 분리 → 1주 관찰 후 삭제"** (안전 bias)

**세션76 Step 1·2 착수 적절성: 동의**
- 둘 다 저공수에 효과 크고, Step 2는 기존 라벨 활용하는 정책 변경이라 가장 빠르게 체감 병목 감소

**놓친 관점 (GPT 신규 지적)**:
- Pruning 후보를 "30일 무고장"만으로 자르지 말고 **최근 수정 이력(해당 훅/공용파일 변경 빈도)**까지 같이 봐야 함
- hook_common.sh나 evidence 공용축을 물고 있는 테스트는 무고장이어도 보호가치 높음
