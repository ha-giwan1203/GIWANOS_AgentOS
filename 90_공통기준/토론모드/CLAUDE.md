# 토론모드 프로젝트

## 목적
Claude가 브라우저에서 ChatGPT 웹 화면을 직접 읽고, 이전 답변을 바탕으로 다음 반박/질문을 생성하여 반자동 토론을 이어가는 코워크 구조.

## 핵심 조건
- API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만 사용
- 사용자는 ChatGPT에 로그인 상태 유지
- 완전 무인 자동화가 아닌 반자동 코워크 (사용자가 주제/방향 결정, Claude가 실행)
- 로그는 로컬 파일로 저장

## 사용자 개입 금지 원칙 (필수)

> **토론모드·공동작업 진행 중 사용자에게 중간 승인/확인을 요청하지 않는다.**

금지 패턴:
- "GPT에게 전송할까요?"
- "이렇게 반영할까요?"
- "CLAUDE.md 업데이트할까요?"
- "이 방향으로 진행할까요?"
- "이견 있으면 말해줘" (사용자에게)

허용되는 유일한 예외 (이 3가지만):
1. 정말 필요한 입력값이 없을 때 (URL, 주제 등)
2. 되돌리기 어려운 외부 실행 (파일 삭제, 원본 덮어쓰기)
3. 사용자가 명시적으로 "검토만", "보내지 마" 지시한 경우

허용 문장 (금지 패턴 대신 사용):
- "이 기준으로 바로 적용한다."
- "합의 반영 후 결과만 보고한다."
- "추가 정보가 없으면 자동 진행한다."

올바른 흐름:
```
사용자 방향 지시
  → Claude가 GPT에 의제 전송
  → GPT 응답 비판적 분석 (하네스 방식)
  → 반박 전송
  → 합의 도출
  → 합의안 즉시 실행 (파일 반영/커밋/푸시)
  → GPT에 실행 결과 공유
  → GPT 추가사항 발생 시 수정 → 재공유 → 재합의 (루프)
  → 추가사항 없으면 완료 보고 (사용자에게)
```
핵심: 합의 → 실행 → GPT 공유 → 추가수정 → 재공유 → 최종합의가 하나의 루틴이다.
GPT 공유 후 추가사항이 나오면 멈추지 않고 수정 → 재공유를 반복한다.
사용자에게 보고하는 건 GPT와의 루프가 완전히 끝난 뒤 1회만.

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
> 반드시 `javascript_tool` + `sleep N` 분리 호출로 루프를 구성한다.
> **sleep 60 같은 긴 고정 대기 금지.**
> 확장추론 표시 selector는 불안정하므로 core 로직에 의존하지 않는다.

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

### 입력 전 미확인 응답 점검 (필수)

> 메시지 전송 전 반드시 실행. 확인 없이 바로 입력하는 것은 금지.

```javascript
const msgs = document.querySelectorAll('article[data-message-author-role="assistant"]');
const lastText = msgs[msgs.length - 1]?.innerText?.slice(0, 100) || '';
```

1. 마지막 assistant 블록 텍스트를 먼저 읽는다
2. 이전에 읽은 내용과 다르면 → 새 응답이 있는 것 → 먼저 읽고 반영
3. 같으면 → 변동 없음 → 예정대로 전송 진행

### GPT 응답 비판적 분석 (필수 — 반박 생성 전)

> **이 단계를 건너뛰면 GPT 프레임에 종속된다. 세션이 바뀌어도 반드시 실행.**

GPT 응답 수신 후, 반박을 작성하기 전에 **주장 분해 → 라벨링 → 채택/버림 판정**을 수행한다.

#### Step 1: 주장 분해
GPT 응답에서 핵심 주장 2~4개를 분리한다.

#### Step 2: 주장별 라벨링 (아래 4개 중 하나)
- **실증됨**: 이번 세션 또는 이전 세션에서 실제 동작 확인
- **일반론**: 이론적으로 맞지만 우리 환경 실증 없음
- **환경 미스매치**: 우리 실행 환경(Claude in Chrome MCP, javascript_tool 매 호출 새 컨텍스트)에 안 맞음
- **과잉설계**: 현재 규모(3~5턴 반자동 토론)에 과함

#### Step 3: 채택/보류/버림 판정
- **채택**: 실증됨 라벨만 해당
- **보류**: 일반론 라벨 — 실제 문제 발생 시 재검토
- **버림**: 환경 미스매치 또는 과잉설계 라벨

> **필수 출력 형식** — 반박문 첫 문단에 아래 구조를 반드시 포함:
> ```
> 채택: [항목]
> 보류: [항목] (있으면)
> 버림: [항목] — [이유]
> ```
> "버림" 또는 "보류"가 0건이면 프레임 검증 실패. GPT 제안을 다시 분해한다.

#### Step 4: 환경 적합성 게이트 (채택 후보만)
채택 후보 각각에 대해:
1. 우리 실행 환경에서 실제 유지되는가?
2. 세션/컨텍스트 지속성이 필요한가?
3. 이번 세션에서 이미 실증된 사실과 충돌하는가?

하나라도 실패하면 채택에서 보류로 강등.

### 반박/질문 생성 규칙
- 위 분해·라벨링·판정 결과를 기반으로 반박 포인트 도출
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
| ChatGPT 응답 미완료 | stop-button 3초 polling, 최대 120초 timeout. 초과 시 사용자에게 보고 |
| 텍스트 추출 실패 | javascript_tool → get_page_text → read_page 순서로 fallback |
| 로그인 만료 | 사용자에게 재로그인 요청 |
| 네트워크 오류 | 로그 기록 후 중단 |

### 금지사항
- ChatGPT API 호출
- 자동 로그인 시도
- find() → form_input 방식으로 입력 (javascript_tool 직접 입력 사용)
- DataTransfer/synthetic paste 기반 입력
- 이전 턴 로그 덮어쓰기
- 프로젝트방 외 일반 대화창에 새 대화 개설
