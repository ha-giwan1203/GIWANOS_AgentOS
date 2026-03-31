# 토론모드 프로젝트

## 목적
Claude가 브라우저에서 ChatGPT 웹 화면을 직접 읽고, 이전 답변을 바탕으로 다음 반박/질문을 생성하여 반자동 토론을 이어가는 코워크 구조.

## 핵심 조건
- API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만 사용
- 사용자는 ChatGPT에 로그인 상태 유지
- 완전 무인 자동화가 아닌 반자동 코워크 (사용자가 주제/방향 결정, Claude가 실행)
- 로그는 로컬 파일로 저장

## 지정 채팅방 원칙 (필수)
- 반드시 지정된 프로젝트방만 사용한다
  - URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
  - 방 이름: `CLAUDE COWORK 업무 자동화 지침만들기`
- `chatgpt.com` 루트 또는 `/c/` 일반 대화창에 임의로 새 대화를 여는 것은 금지
- 기존 대화가 있으면 반드시 해당 URL(chat_url)로 이동해서 이어서 진행
- 새 대화가 필요한 경우에도 반드시 위 프로젝트 하위에서만 개설

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

#### 입력 방식 (우선순위)
```
1순위: javascript_tool → focus() → execCommand('insertText', false, text)
       - contenteditable에서 가장 안정적. undo buffer 보존
       - 전송버튼 활성화까지 한 번에 처리됨 (2026-03-31 실증)
2순위: textContent 직접 삽입 + new InputEvent('input', {bubbles:true, composed:true}) dispatch
       - execCommand 실패 시 fallback
금지:  DataTransfer/synthetic paste 기반 입력 (isTrusted=false → 앱이 무시)
금지:  find() → form_input 방식 (느림, React 이벤트 미트리거)
```

#### 전송
```javascript
const btn = document.querySelector('[data-testid="send-button"]');
if (btn && !btn.disabled) btn.click();
```
> 클릭 전 disabled 상태 확인 필수.

#### 응답 완료 감지
```
방식:    stop-button 유무 확인 (polling)
완료:    document.querySelector('[data-testid="stop-button"]') === null
간격:    3초
timeout: 최대 120초 (GPT 확장추론 대응)
```
> MutationObserver는 javascript_tool 매 호출 새 컨텍스트라 상태 유지 불가. 오탐 실제 발생 전까지 도입하지 않는다.

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

### GPT 응답 비판적 분석 (필수 — 반박 생성 전)

> **이 단계를 건너뛰면 GPT 프레임에 종속된다. 세션이 바뀌어도 반드시 실행.**

GPT 응답 수신 후, 반박을 작성하기 전에 아래 3개 질문에 먼저 답한다:

1. **실증 검증**: 이 제안이 우리 환경(Claude in Chrome MCP, javascript_tool, 반자동 토론)에서 실제로 작동하는가? 일반론이 아닌가?
2. **과잉설계 검증**: 현재 규모(3~5턴 토론)에 비해 과한 구조를 제안하는가? 실증된 간단한 방식이 이미 있는데 복잡한 대안을 제시하는가?
3. **프레임 검증**: GPT가 설정한 문제 정의와 선택지 자체가 맞는가? 다른 방식으로 문제를 볼 수 있는가?

3개 중 하나라도 "아니오"면 해당 지점을 반박에 포함한다.
3개 모두 "예"라도, GPT 결론을 그대로 수용하지 말고 최소 1개 이상 이견이나 보완점을 찾는다.

### 반박/질문 생성 규칙
- GPT 응답의 핵심 주장을 3줄 이내로 요약
- 위 비판적 분석 결과를 기반으로 반박 포인트 2~3개 도출
- 반박은 "구체적 근거 + 대안 제시" 구조
- 감정적 표현 금지, 논리적 구조만 사용
- 반박 생성 후 승인 없이 자동 전송 (메모리 피드백 기준)

### 로그 저장 구조
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

### 오류 대응
| 상황 | 대응 |
|------|------|
| ChatGPT 응답 미완료 | 15~30초 대기 후 stop-button 확인, 3회 실패 시 중단 |
| 텍스트 추출 실패 | read_page → find 순서로 fallback |
| 로그인 만료 | 사용자에게 재로그인 요청 |
| 네트워크 오류 | 로그 기록 후 중단 |

### 금지사항
- ChatGPT API 호출
- 자동 로그인 시도
- find() → form_input 방식으로 입력 (javascript_tool 직접 입력 사용)
- DataTransfer/synthetic paste 기반 입력
- 이전 턴 로그 덮어쓰기
- 프로젝트방 외 일반 대화창에 새 대화 개설
