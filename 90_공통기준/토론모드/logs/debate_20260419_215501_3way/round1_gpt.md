# Round 1 — GPT 답변

## 의제
클로드코드(Claude Code) 운영 정밀 분석

## 사용자 프롬프트
"클로드코드 정밀 분석"

## GPT 응답 (len=3100)

결론: 클로드코드는 설계는 꽤 잘 잡혔는데, 실제 운영은 게이트 과밀·문서 드리프트·증빙 의존 과다 때문에 마찰이 큰 상태입니다. 완성도가 낮다기보다, 통제장치가 실무 흐름을 자꾸 잡아먹는 쪽입니다.

이유 1: 구조 자체는 나쁘지 않습니다. 루트 기준에서 Git 원본 우선, 완료 판정 분리, permissions와 hook 역할 분리, 훅 등급(advisory/gate/measurement) 구분까지 문서화돼 있고, 공통 라이브러리 hook_common.sh에 로그·incident·session/evidence·completion 판정·relevant change 수집이 모여 있어 아키텍처 일관성은 있습니다.

이유 2: 문제는 운영 부채가 너무 많이 쌓였다는 점입니다. incident ledger를 보면 반복되는 미해결 이슈가 evidence_gate, commit_gate, navigate_gate, harness_gate, final_check meta_drift에 계속 누적됩니다. 특히 최근에도 STATUS(2026-04-18) < TASKS(2026-04-19) 드리프트, tasks_handoff.req 미해결, skill_read.req / identifier_ref.req 미해결, map_scope.req 미해결, CLAUDE.md 미읽기, MES access without SKILL.md read가 반복됩니다. 이건 "보호가 잘 된다"가 아니라 시스템이 계속 같은 자리에서 헛바퀴 돈다는 증거입니다.

핵심 병목 1: commit_gate.sh는 꽤 강합니다. write_marker가 있으면 TASKS/HANDOFF 동봉 없이는 commit을 막고, 훅·settings 변경이 섞이면 --full로 승격하며, 실패 시 incident를 남기고 fingerprint suppress까지 겁니다. 설계는 맞는데, ledger상 commit_gate 관련 incident가 반복되고, 60분 캐시라서 settings 정리 직후 재검증 민감도는 떨어집니다. 성능을 택한 설계인데, 지금처럼 settings 드리프트가 잦은 환경에서는 정리 확인 루프가 느립니다.

코드 레벨에서 가장 불안한 지점은 hook_common.sh입니다. 여기 의존도가 너무 높습니다. safe_json_get, completion claim 판정, evidence/session 관리, relevant change 판정, incident 기록, wrapper가 전부 여기에 몰려 있습니다. 이런 공용축은 좋은데, 실제 구현은 sed/tr 기반 JSON 파싱을 많이 써서 복잡한 JSON이나 escaped edge case에서 깨질 가능성이 있습니다. 아직 ledger에서 이걸 직접 찍은 장애는 못 봤지만, 구조상 single point of fragility입니다.

추가 실운영 문제 3가지:
첫째, python3 의존 잔존 경고가 최근까지 반복됩니다. Windows Git Bash 고려를 문서에 써놨는데도 핵심 훅들이 여전히 python3에 기대고 있습니다. portable하지 않습니다.

둘째, debate 검증 체인이 깨져 있습니다. debate_verify에서 result.json 파싱 실패와 step5_final_verification.md 누락이 반복됩니다. 토론모드 품질검증이 "있다"가 아니라 증빙 파일 연결이 자꾸 끊깁니다.

셋째, README/STATUS/AGENTS_GUIDE와 settings 수치 불일치가 계속 나옵니다. 즉 시스템 설명서가 현재 실물과 자주 안 맞습니다. 이런 상태면 새 세션/다른 에이전트가 들어왔을 때 오판정 나기 쉽습니다.

판정: 부분정합입니다. 구조 설계는 살아 있고 게이트 분리 방향도 맞습니다. 하지만 지금 실물 기준으로는 운영 부채와 반복 경고가 많아 "정교하게 잘 굴러간다" 수준은 아닙니다. 최근 ledger 기준으로는 문서 드리프트와 evidence 미해결이 계속 남아 있어 안정 운영 상태로 보긴 어렵습니다.

다음 행동 권고:
a) incident_ledger부터 정리해서 반복 미해결 항목 5종(STATUS drift, tasks_handoff.req, skill_read.req, map_scope.req, navigate_gate) 먼저 끊기
b) README/STATUS/AGENTS_GUIDE를 settings와 자동 동기화하는 --fix 루틴을 commit 전에 강제
c) evidence_gate에 commit_gate처럼 fingerprint suppress/쿨다운 추가

## GPT Round 1 교차 검증 답 (Gemini 원문 + Claude 실물 검증 대조 후)

**Gemini 답변 1줄 검증: 동의** — 분석 큰 방향은 유지되지만 60분 캐시는 자신의 오류. 나머지는 "운영 마찰 과다" 해석이 더 정확.

**주장 3 "60분 캐시" 버림 수용**: 자신의 오판. 60분 = permissions_sanity.sh CACHE_TTL=3600, commit_gate.sh의 60 = incident suppress grace window. 같은 개념 아님.

**Policy 현실성 신규 지적 — 별도 의제 승격 타당**: 근거 충분. 단 "전부 false positive" 단정은 과함. **정확한 표현: "policy-workflow mismatch 의심"** (세련화 제안).

**권 b 자동 --fix 재철회 (합의 수용)**: 범용 --fix 자동화는 위험. STATUS/TASKS/HANDOFF 상태 원본은 사람이 판정. 자동화 허용해도 **README/AGENTS_GUIDE 같은 파생 문서만 preview 기반 제한**.

**GPT 새 방향 제안**: "게이트 완화"가 아니라 **"정책 기준 재설계"** — evidence_gate/commit_gate/navigate_gate 정책-현업 정합성 재검토 찬성.

## GPT 최종 설계안 검증

**판정: 동의** — "Policy-Workflow Mismatch 재정의" 승격이 현 실물과 가장 잘 맞음

- 가장 위험: **즉시 1 evidence_gate Policy 재검토** (측정 없이 건드리면 통제 무너짐)
- 가장 확실: **즉시 3 파생 문서 preview 절충** (상태 원본 보호 + 부작용 최소)
- Round 2 포함: 주장 4·5·6 **모두 제외**

**수정 제안**:
1. 즉시 1번 앞에 **"측정 프로토콜 확정"** 단계 추가 — true_positive / FP 의심 / 정상중간과정 라벨링 규칙 고정
2. evidence_gate를 한 덩어리가 아닌 **tasks_handoff / skill_read / map_scope / auth_diag 하위 정책별 분해** 분석
