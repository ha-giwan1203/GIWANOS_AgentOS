# 토론모드 프로젝트 (Reference 문서)

> **이 파일은 Reference다. Primary는 ENTRY.md.**
> ENTRY.md의 NEVER 규칙이 최우선. 이 문서는 상세 배경·selector·fallback 참조용.
> 등급: [NEVER] 위반=버그 / [SHOULD] 최선 노력 / [MAY] 선택

## 목적
Claude가 브라우저에서 ChatGPT 웹 화면을 직접 읽고, 이전 답변을 바탕으로 다음 반박/질문을 생성하여 반자동 토론을 이어가는 코워크 구조.

## 핵심 조건
- [NEVER] API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만 사용
- [SHOULD] 사용자는 ChatGPT에 로그인 상태 유지
- [SHOULD] 완전 무인 자동화가 아닌 반자동 코워크 (사용자가 주제/방향 결정, Claude가 실행)
- [MAY] 로그는 로컬 파일로 저장

## 사용자 개입 금지 + 실행 루프 (hooks 강제)

> stop_guard.sh가 금지 문구를 차단한다. prompt_inject.sh가 체크리스트를 주입한다.

[NEVER] 사용자에게 중간 승인 요청 금지. 예외: 입력값 부족 / 비가역 실행 / 명시적 "검토만" 지시.

실행 루프: 방향 지시 → GPT 토론 → 합의 → 즉시 실행 → GPT 공유 → 추가수정 시 재공유 루프 → 루프 완료 후 사용자 보고 1회.

## 지정 채팅방 원칙
- [NEVER] 프로젝트방 외 사용 금지
  - URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
  - 방 이름: `CLAUDE COWORK 업무 자동화 지침만들기`
- [NEVER] `chatgpt.com` 루트 또는 `/c/` 일반 대화창에 임의로 새 대화 개설 금지
- [SHOULD] 새 대화가 필요한 경우에도 위 프로젝트 하위에서만 개설

### 채팅방 입장 규칙
- [SHOULD] 프로젝트 페이지 진입 후 **채팅 목록의 첫 번째(최상단) 대화방**에 바로 입장
- [SHOULD] 특정 대화를 지정받지 않는 한, 항상 첫 번째 방 = 최신 대화로 진입
- [SHOULD] 기존 대화 URL을 별도 기억/하드코딩하지 않는다 — 매번 목록에서 첫 번째를 선택

#### [SHOULD] 세션 재진입 시 탭 재사용 (신규 탭 중복 방지)
새 Claude 세션 시작 시 브라우저 탭을 먼저 확인한다.

```
1. tabs_context_mcp → 현재 열린 탭 목록 확인
2. chatgpt.com/g/g-p-69bca... URL 포함 탭 있으면 → switch (새 탭 열지 않음)
3. 없으면 → navigate로 프로젝트 URL 진입 후 아래 '대화 URL 추출' 절차 실행
```

> 이유: Claude 세션은 브라우저 상태를 기억하지 않으나, 탭이 이미 열려있으면 재사용해야 불필요한 새 창 생성을 막을 수 있다.

#### 대화 URL 추출 (클릭 대신 JS 직접 추출 — 2026-04-01 실증)

프로젝트 페이지에서 대화 목록 클릭은 React 이벤트 미트리거로 실패할 수 있다.
[NEVER] **클릭 시도 금지. 반드시 JS로 URL을 추출한 뒤 navigate()로 진입한다.**

```javascript
// 핵심: 반드시 main 영역에서 추출. nav(사이드바)의 a[href*="/c/"]와 혼동 금지.
// 프로젝트 대화 URL 형식: /g/g-p-.../c/... (사이드바는 /c/... 만)
const main = document.querySelector('main');
const links = main ? main.querySelectorAll('a[href*="/c/"]') : [];
const url = links.length > 0 ? links[0].href : null;
url;  // → navigate()에 전달
```

> **주의 (2026-04-01 실증)**: `nav a[href*="/c/"]`는 사이드바 일반 대화 목록이다.
> 프로젝트 전용 대화는 `main` 영역 안에만 있고, URL에 `/g/g-p-.../c/...` 패턴을 포함한다.
> 사이드바에서 찾으면 엉뚱한 대화방에 진입하게 되므로 **반드시 `main` 스코프로 제한**한다.

```
실행 순서:
1. navigate → 프로젝트 URL (채팅 목록 페이지)
2. javascript_tool → 위 스크립트로 첫 번째 대화 URL 추출
3. navigate → 추출된 URL로 대화방 진입
```

> 클릭 방식이 아닌 URL 추출+navigate 방식을 쓰는 이유:
> ChatGPT 프로젝트 페이지의 대화 목록은 `<a>` 태그이지만 React 이벤트 바인딩 때문에
> DOM 클릭으로는 안정적으로 진입할 수 없다. href를 직접 뽑아 navigate하면 100% 진입된다.

## 작업 흐름

### 기본 루프
1. 사용자가 주제와 초기 프롬프트를 제공
2. Claude가 ChatGPT 브라우저 탭을 열고 프롬프트 입력
3. ChatGPT 응답 대기 → 응답 텍스트 읽기
4. Claude가 응답을 분석하고 반박/질문 생성
5. 생성된 반박을 ChatGPT에 입력
6. 3~5 반복 (설정된 턴 수만큼)
7. 전체 로그 저장

### 브라우저 작업 상세
- ChatGPT URL: https://chatgpt.com
- 프로젝트 URL: https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/

#### 고정 Selector (2026-03-31 실증)
```
입력창:      #prompt-textarea              (contenteditable DIV)
전송버튼:    [data-testid="send-button"]
중지버튼:    [data-testid="stop-button"]   (응답 중에만 존재)
응답 노드:   [data-message-author-role="assistant"]
```
> selector 깨지면 그때 갱신. 미리 fallback 체인 짜지 않는다.

#### 입력+전송 (1회 JS 호출로 통합)
```javascript
// 입력과 전송을 하나의 javascript_tool 호출로 처리 (v3 최적화)
const el = document.querySelector('#prompt-textarea');
el.focus();
document.execCommand('insertText', false, text);
// 전송 (100ms 후 버튼 활성화 대기)
setTimeout(() => {
  const btn = document.querySelector('[data-testid="send-button"]');
  if (btn && !btn.disabled) btn.click();
}, 100);
```
> 입력과 전송을 분리하지 않는다. 1회 JS 호출로 완결.
> 버튼이 없거나 disabled면 1초 wait 후 전송만 별도 재시도.

**fallback (execCommand 실패 시)**:
```
textContent 직접 삽입 + new InputEvent('input', {bubbles:true, composed:true}) dispatch
```
[NEVER] 금지: DataTransfer/synthetic paste 기반 입력 (isTrusted=false → 앱이 무시)
[NEVER] 금지: find() → form_input 방식 (느림, React 이벤트 미트리거)

#### 응답 완료 감지 (적응형 polling)
```
방식:    stop-button 유무 확인 (polling)
완료:    document.querySelector('[data-testid="stop-button"]') === null

적응형 간격 (3단):
  0~20초:   sleep 5  (일반 응답 빠르게 캐치)
  20~60초:  sleep 10 (중간 구간)
  60초~:    sleep 15 (확장추론 대응)
timeout:    최대 300초 (확장추론 5분 대응)
```
> CDP 45초 timeout 때문에 javascript_tool 안에서 setInterval/Promise 기반 polling 불가.
> [NEVER] 반드시 `javascript_tool` + `sleep N` 분리 호출로 루프를 구성한다. (JS 내부 polling 금지)
> [NEVER] **sleep 60 같은 긴 고정 대기 금지.**
> 확장추론 표시 selector는 불안정하므로 core 로직에 의존하지 않는다.

#### GPT 대기 중 병행 작업 (v3)
> GPT 응답 대기(30~60초) 동안 background Agent로 독립 작업을 병행할 수 있다.
> Agent 도구는 독립 컨텍스트에서 실행되므로 세션 충돌 없음 (GPT 합의 2026-04-02).
> 단, PreToolUse hook의 Task matcher가 subagent에도 적용될 수 있으므로 hook 지연만 주의.
> [NEVER] 메인 세션과 컨텍스트는 분리되나, 동일 대상 파일·로그·출력물 동시 수정은 금지.

#### 최신 응답 읽기
```javascript
const msgs = document.querySelectorAll('article[data-message-author-role="assistant"]');
msgs[msgs.length - 1].innerText;
```
> querySelectorAll + 마지막 노드 선택. article 태그 명시로 잡음 방지. :last-of-type는 형제 구조 변경에 취약하므로 사용하지 않는다.

### 최신 답변 읽기 방식
1. javascript_tool로 마지막 assistant 노드 직접 추출 (위 고정 selector 참조)
2. 텍스트가 너무 길거나 잘리면 get_page_text로 전체 페이지 텍스트 추출 후 파싱
3. 파싱 실패 시 read_page로 DOM 구조에서 마지막 메시지 요소 탐색

### [NEVER] SEND GATE — 전송 직전 미확인 응답 점검

> **이 게이트를 통과하지 않으면 전송 금지.** 메시지 입력(execCommand) 전에 반드시 실행.
> 2026-04-06 GPT 합의: 체크리스트만으로 부족, send 직전 하드 게이트로 승격.

```javascript
// SEND GATE: 반드시 전송 직전에 실행
const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
const lastText = msgs[msgs.length - 1]?.innerText?.slice(0, 100) || '';
const stopBtn = document.querySelector('[data-testid="stop-button"]');
JSON.stringify({lastSnippet: lastText, isGenerating: !!stopBtn});
```

1. 마지막 assistant 블록 텍스트 100자를 읽는다
2. GPT가 아직 생성 중(stop-button 존재)이면 → 대기
3. 이전에 읽은 내용과 다르면 → **새 응답 전체 읽기 → 하네스 재계산 → 반박문 재작성** 후 전송
4. 같으면 → 변동 없음 → 예정대로 전송 진행
5. [NEVER] 이 절차를 건너뛰고 바로 execCommand 호출하는 것은 금지

### [NEVER] GPT 응답 비판적 분석 — 하네스 방식

> stop_guard.sh가 채택/보류/버림 누락을 차단한다. prompt_inject.sh가 체크리스트를 주입한다.

[NEVER] GPT 응답 → 주장 2~4개 분해 → 라벨링 → 채택/보류/버림 판정 → 반박 생성. 생략 금지.

라벨: 실증됨 / 일반론 / 환경 미스매치 / 과잉설계
판정: 채택(실증만) / 보류(일반론) / 버림(미스매치+과잉)

[NEVER] **필수 출력**: 반박문 첫 문단에 `채택:` `보류:` `버림:` 포함. 누락 금지.
[SHOULD] **환경 게이트**: 채택 후보는 (1)우리 환경 유지 (2)세션 지속성 불필요 (3)실증과 미충돌 통과 필수.

#### [SHOULD] 사용자 보고 축약 (v3)
- 하네스 분석 결과를 사용자에게 보여줄 때 **매턴 표 대신 1줄 요약**으로 축약한다.
- 형식: `채택 N건 / 보류 N건 / 버림 N건 — [핵심 판정 이유 1줄]`
- 상세 분해·라벨링은 반박문(GPT에 전송하는 텍스트) 안에만 포함한다.
- [MAY] 로그 파일에는 상세 분석을 저장한다.

### [NEVER] GPT 실물 검증 공유 규칙 (v3)
> **구현 → 커밋+푸시 → SHA 포함 공유**를 1회로 완결한다.
> [NEVER] 커밋 없이 결과만 먼저 공유하고 GPT가 SHA를 요구하면 다시 커밋+공유하는 2중 작업 금지.

순서:
1. 구현 완료
2. `git add` → `git commit` → `git push` (한 번에)
3. GPT에 커밋 SHA + 파일 경로 포함하여 공유
4. GPT 판정 대기

### [SHOULD] 반박 생성 규칙
- 분해·판정 기반 반박 포인트 도출. 근거 + 대안 구조. [NEVER] 승인 없이 자동 전송 (중간 승인 요청 금지).

### [MAY] 로그 저장 구조
```
logs/
├── debate_YYYYMMDD_HHMMSS.md
└── debate_YYYYMMDD_HHMMSS.json
```

MD 로그 형식:
```
# 토론 로그
- 주제: {주제}
- 시작: {시각}
- 턴 수: {N}

## Turn 1 (Claude → GPT)
{입력 프롬프트}

## Turn 1 (GPT 응답)
{GPT 응답 텍스트}

## Turn 2 (Claude 반박)
{반박 내용}
...
```

JSON 로그: 턴별 타임스탬프, 입력/출력, 토큰 추정, 오류 여부

### [SHOULD] 오류 대응
| 상황 | 대응 |
|------|------|
| ChatGPT 응답 미완료 | 적응형 polling(5/10/15초), 최대 300초 timeout. 초과 시 사용자에게 보고 |
| 텍스트 추출 실패 | javascript_tool → get_page_text → read_page 순서로 fallback |
| 로그인 만료 | 사용자에게 재로그인 요청 |
| 네트워크 오류 | 로그 기록 후 중단 |

### 금지사항
- [NEVER] ChatGPT API 호출
- [NEVER] 자동 로그인 시도
- [NEVER] find() → form_input 방식으로 입력 (javascript_tool 직접 입력 사용)
- [NEVER] DataTransfer/synthetic paste 기반 입력
- [SHOULD] 이전 턴 로그 덮어쓰기
- [NEVER] 프로젝트방 외 일반 대화창에 새 대화 개설
