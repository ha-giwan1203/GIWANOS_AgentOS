# Q4 Round 1 — GPT (gpt-5-5-thinking)

## 결론
Q4 = **A안 채택** (단, navigate_page/new_page만 매처 확장 + select_page 등은 제외하는 **최소보강안**)

## 주요 주장 (라벨 + 증거)

### 1. [실증됨] navigate_gate.sh 구 MCP 단일 매처 구조
- navigate_gate.sh 주석: `mcp__Claude_in_Chrome__navigate` 명시
- settings.json PreToolUse matcher 단일 연결
- chatgpt.com URL 진입 시 debate_claude_read.ok 없으면 send_block 차단

### 2. [실증됨] 세션105 chrome-devtools-mcp 전환 후 신규 진입 경로 커버 안 됨
- gpt-send.md 현재: new_page / navigate_page / select_page(bringToFront=true)
- 기존 navigate(url, tabId) 재호출 hack → CDP 네이티브 전환
- 현재 navigate_gate는 신규 진입 경로 미커버

### 3. [실증됨] 11건 incident 해석
- 보안 의도에 맞는 정당 차단 8~11건 / false positive 0~3건 추정
- 원문 샘플 이번 조회 미확인 (실측 한계)

### 4. [환경미스매치] Q4 session_init.md main 미반영
- 아직 push 안 됨. 평가는 기존 실물 파일 기준
- 단, 구 MCP 단일 매처 / 신규 MCP 우회 구조는 다른 파일로 충분히 확인됨

### 5. [일반론] A안은 보안 커버리지 + 유지보수성 균형점
- new_page / navigate_page는 URL 진입 동작 → gate 대상
- select_page는 foreground 전환이라 URL 진입 아님 → gate 제외
- 오탐 축소 + 훅 복잡도 최소 증가

## 반대 안 약점

### B안 — 과잉설계
- permissions.deny로 skill-only 강제 시 "현재 호출이 gpt-send/gemini-send 내부인지" 판별 필요
- context 판별 불안정 시 정상 스킬 실행도 막음
- 지금 필요한 건 우회 경로 보강이지 권한 체계 재설계 아님

### C안 — 보안 커버리지 후퇴
- navigate_gate 폐기 + 스킬 evidence만 강화 시 MCP 직접 호출 경로 재개방
- 본질 "신규 MCP가 gate 밖에 있음" → 훅 제거 시 우회 방지 목적 자체 포기

## 착수 조건
1. Q4 session_init.md Git main push 확인
2. navigate_gate.sh + settings.json 수정 범위를 chrome-devtools-mcp navigate_page, new_page 매처 추가로 한정
3. select_page, evaluate_script, take_snapshot, click, fill은 gate 대상 제외

## 완료 기준
- settings.json PreToolUse에 신규 matcher 2개 추가:
  - `mcp__chrome-devtools-mcp__navigate_page`
  - `mcp__chrome-devtools-mcp__new_page`
- navigate_gate.sh가 도구별 URL 필드 파싱:
  - old: tool_input.url / url
  - new_page: tool_input.url
  - navigate_page: tool_input.url, **type="url"일 때만** 검사
- chatgpt.com 진입 + debate_claude_read.ok 없음 → deny
- chatgpt.com 외 URL 또는 select_page → 통과
- hook count + AGENTS_GUIDE 자동 섹션 갱신

## 검증 조건
- 네거티브: marker 없이 navigate_page chatgpt.com 진입 시 차단
- 포지티브: marker 후 동일 진입 통과
- 비대상: select_page(bringToFront=true)는 차단되지 않음
- 회귀: 기존 Claude_in_Chrome__navigate 차단 유지

## 효과성 평가 (재라운드 트리거)
- 적용 후 7일간 navigate_gate send_block 0~2건: 정상
- 3건 이상: raw incident 샘플링 후 Round 2 재검토

## 최종 판단
A안 채택. C안은 너무 풀고, B안은 너무 묶음. 지금은 "새 길만 문지기 앞에 다시 연결"하면 됨.
