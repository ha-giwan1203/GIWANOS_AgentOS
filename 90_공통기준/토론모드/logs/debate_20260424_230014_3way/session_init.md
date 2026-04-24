# Q4 navigate_gate 감지 기준 재검토 — 3자 토론 세션 초기화

- 날짜: 2026-04-24 23:00 KST
- 모드: 3way (Claude × GPT × Gemini)
- 상위 배경: 세션105 Q3 auto-fix 분류 결과 navigate_gate send_block 11건 → 신규 Q4 후보 등록
- 로그 경로: `90_공통기준/토론모드/logs/debate_20260424_230014_3way/`
- 최대 라운드: 3

## 핵심 발견 (실증됨)

세션105 chrome-devtools-mcp 전환 후 **새 MCP가 navigate_gate를 우회**한다:
- `navigate_gate.sh` 매처: `mcp__Claude_in_Chrome__navigate` (단일)
- 신규 사용 도구: `mcp__chrome-devtools-mcp__navigate_page`, `mcp__chrome-devtools-mcp__new_page`
- 결과: 세션105 Round 2에서 CLAUDE.md 읽기 마커 없이도 ChatGPT 진입 성공 — 게이트 동작 안 함
- 기존 11건 incident는 전부 구 MCP(Claude_in_Chrome) 사용 시기

## 의제 Q4

**선택지 3개**

**A안 — 매처 확장 (보수적)**
- navigate_gate.sh 매처를 chrome-devtools-mcp의 navigate_page + new_page에 추가
- URL 필드 파싱 로직은 각 도구별 재확인 필요 (payload 구조 다름)
- 보안 의도 유지, 신규 MCP도 동일 게이트 적용

**B안 — skill-only 강제 (우회 방지)**
- A안 + 추가 강화: MCP navigate 계열 툴 직접 호출 자체를 차단 (permissions.deny)
- gpt-send/gemini-send 스킬만 호출 허용
- 스킬 내부는 chrome-devtools-mcp 직접 호출하므로 허용 경로 유지 (skill context 판별 필요)

**C안 — 게이트 폐기 + 스킬 내부 evidence 강화 (단순화)**
- navigate_gate.sh 완전 폐기
- 대신 gpt-send/gemini-send 스킬 Step 0에 "debate_claude_read.ok 확인" 명시 + 없으면 스킬 자체 중단
- 훅 수 감축, 로직을 스킬에 집중

## 평가 포인트 (양측 요청)

1. 각 안의 장단점 — 보안 커버리지 vs 오탐률 vs 유지보수성
2. 실측 근거 — 11건 incident 중 "정당한 차단"과 "false positive"의 비율 추정
3. 세션105 chrome-devtools-mcp 전환 맥락에서 어느 안이 가장 적합한지
4. 재라운드 트리거 조건 (실행 후 effectiveness 평가 방법)

## issue_class
- Q4: **B** (hook matcher 변경 + 실행 흐름·판정 분기 영향)

## 초기 Claude 편향 (공개)

개인 편향으로 A안(매처 확장)이 가장 안전해 보이나, C안의 단순화 논리도 강력하다. Q1 "advisory 유지" 원칙과 일관성 있는 방향 찾기 목적. 양측 답변으로 편향 교정 필요.
