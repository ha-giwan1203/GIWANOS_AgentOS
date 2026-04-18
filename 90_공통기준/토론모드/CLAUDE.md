# 토론모드 코어 규칙

> 앱 운영 기준: `APP_INSTRUCTIONS.md`
> 실행 절차: `debate-mode/SKILL.md`
> 기술 상세: `REFERENCE.md`
> 전역 상태 원본: `../업무관리/TASKS.md`
> 토론모드 내부 작업 목록: `TASKS.md`

> **코어: 이 파일**

## 진입점
**[MUST] 토론/공동작업/공유 관련 요청 시 반드시 `/debate-mode` 스킬로 진입한다.**
- 2자 토론 트리거: "토론", "토론모드", "GPT와 토론", "debate-mode", "공동작업", "공유"
- **3자 토론 트리거**: "3자 토론", "삼자 토론", "3-way", "3-party", "Claude×GPT×Gemini", "Gemini도 포함", "상호 감시", "교차 검증 토론"
- `Skill(skill="debate-mode")` 호출 — 수동 navigate/gpt-send 사용 금지
- navigate_gate 훅이 CLAUDE.md 미읽기 시 ChatGPT 진입을 차단한다

## 목적
Claude가 브라우저에서 ChatGPT 화면을 직접 읽고 반자동 토론을 이어가는 코워크 구조.
- [NEVER] API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만
- [NEVER] 사용자 중간 승인 요청 금지 (예외: 입력값 부족 / 비가역 / "검토만" 지시)
- [NEVER] 토론방에 전송하는 자연어는 한국어만 사용

## 지정 채팅방
- 프로젝트 URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c-gpt-keulrodeu-eobmu-jadonghwa-toron/project`
- [NEVER] 프로젝트방 외 새 대화 개설 금지
- [MUST] 매 세션 시작 시 프로젝트 URL에서 최상단(최신) 채팅방을 자동 탐지하여 `debate_chat_url` 갱신
- [NEVER] 이전 세션의 debate_chat_url 값을 검증 없이 재사용 금지
- [NEVER] 일반 채팅 URL(`/c/` 단독)을 프로젝트 채팅방으로 사용 금지 — 프로젝트 slug 포함 URL만 허용

## 실행 루프
1. **토론 로직만 담당**: 독립 점검 → 하네스 분석 → 반박 생성 → 로그 기록
2. **전송**: `Skill(skill="gpt-send", args="메시지")` — 탭 준비/진입/SEND GATE/입력/전송/응답읽기 일괄
3. **응답 읽기**: `Skill(skill="gpt-read")` — 응답 완료 확인 + 최신 텍스트 반환
4. 하네스 분석 → 반박 생성 → gpt-send → 반복

> **[NEVER] debate-mode 안에서 Chrome MCP 도구 직접 호출 금지.**
> tabs_context_mcp, navigate, javascript_tool, get_page_text, find, computer 등
> 브라우저 조작은 전부 gpt-send/gpt-read 내부에서 처리한다.

## 고정 Selector (gpt-send/gpt-read 내부 참조용)
```
입력창:      #prompt-textarea              (contenteditable DIV)
전송버튼:    [data-testid="send-button"]   (텍스트 입력 후 표시될 수 있음)
대체확인:    #composer-submit-button       (동일 버튼 id)
idle 상태:   [data-testid="composer-speech-button"]  (빈 입력창에서 허용)
중지버튼:    [data-testid="stop-button"]   (응답 중에만 존재)
응답 노드:   [data-message-author-role="assistant"]
```

## 언어 규칙
- [NEVER] 질문/반박/검증 요청/완료 보고/재판정 요청을 영어 문장으로 보내지 않는다.
- [ALLOW] code block, selector/data-testid, 파일 경로, commit SHA, 에러 원문 최소 인용만 literal 유지 가능
- [ALLOW] 에러 원문 최소 인용은 `오류 원문:` 또는 `에러 원문:` 라벨 1줄로 제한
- [SHOULD] GPT가 영어로 답하면 `영어 없이 한국어만으로 다시 정리해줘.`를 1회 요청한 뒤 계속 진행

## 하네스 분석 (NEVER — 생략 금지)
GPT 응답 → 주장 2~4개 분해 → 라벨링(실증됨/일반론/환경미스매치/과잉설계) → 채택/보류/버림
- 반박문 첫 문단에 `채택:` `보류:` `버림:` 필수
- 사용자 보고는 1줄 요약: `채택 N건 / 보류 N건 / 버림 N건`

## 상호 감시 프로토콜 (3자 토론 시 — NEVER 생략)

3자 토론(Claude × GPT × Gemini) 시 **단일 모델 단독 통과 금지**. 세션66 사용자 지적으로 신설.

**라운드별 교차 검증 강제**:
1. GPT 답 → 다음 메시지에 Gemini의 1줄 검증 첨부 ("동의 / 이의 / 검증 필요")
2. Gemini 답 → 다음 메시지에 GPT의 1줄 검증 첨부
3. Claude 종합·설계 → 양측의 1줄 검증 받은 후 채택
4. 단일 모델 동의로 합의 종결 금지 — 최소 2/3 검증 통과 시만 채택
5. Claude 단독 설계 결정 금지 — GPT/Gemini가 Claude 설계 반박 의무

**검증 누락 시**: 즉시 중단 + 사용자 보고 + 라운드 재실행

**왜 필요**: Claude 단독 검증자 구조는 Claude 검증 누락 시 통과되는 결함. 세션66 5라운드에서 실제 발생. 자세한 배경: 메모리 `project_three_tool_workflow.md` "상호 감시 프로토콜" 섹션

## 백그라운드 탭 Throttling 대응 (세션70 실증 — NEVER 생략)

**증상**: Chrome은 백그라운드 탭의 JavaScript 타이머·네트워크·DOM 업데이트를 throttling한다. ChatGPT/Gemini 탭이 백그라운드일 때 응답 DOM 생성이 지연되거나 누락되어 감지 실패가 발생한다. 세션69 Gemini synthesis 미수령 원인이 이것이었다.

**대응 (필수)**:
1. **전송/읽기 직전 대상 탭 활성화**: `navigate(url=현재URL, tabId=대상_tabId)` 재호출로 해당 탭을 foreground로 올린다. 동일 URL navigate는 페이지 상태를 보존하면서 탭 포커스만 전환한다.
2. Chrome MCP는 별도 tab activate/focus API를 제공하지 않는다. `navigate` 재호출이 유일한 회피 경로다.
3. 응답 감지 적응형 polling(3/5/8초, 최대 300초)에서 stop-button·aria-disabled 상태 변화를 감지 못 하면 **navigate reload 1회 재시도** 후 다시 polling.
4. 2회 연속 감지 실패 시 "탭 throttling 복구 실패 — 사용자 수동 활성화 필요" 보고.

**3자 토론 특이사항**:
- 양측 모델(GPT·Gemini) 중 한쪽은 항상 백그라운드가 된다.
- 매 전송/읽기 전 대상 탭 navigate 재호출 필수. 병렬 폴링 금지(백그라운드 쪽 필연 지연).
- GPT 전송 → GPT 수신 → Gemini 탭 activate navigate → Gemini 전송 → Gemini 수신 순으로 직렬 실행.

**관련 스킬**: `/gpt-send`, `/gpt-read`, `/gemini-send`, `/gemini-read` 모두 Step에 탭 활성화 navigate 단계가 명시되어야 한다.

## GPT 실물 검증 공유 (NEVER)
구현 → `git commit` → `git push` → SHA + `git show --stat` 요약 포함 공유 (한 번에). 커밋 없이 먼저 공유 금지.

## 금지사항
- [NEVER] ChatGPT API 호출
- [NEVER] DataTransfer/synthetic paste 입력
- [NEVER] JS 내부 polling (sleep 분리 호출만)
- [NEVER] sleep 60 같은 긴 고정 대기
- [NEVER] CDP 스크립트 사용 (cdp_chat_send.py 등 — 폐기됨)

## 상세 참조
selector 목록, fallback 체인, 오류 대응, 로그 형식, 병행 작업 규칙 → `REFERENCE.md`
