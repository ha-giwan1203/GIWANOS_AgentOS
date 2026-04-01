# 토론모드 프로젝트

## 목적
Claude가 브라우저에서 ChatGPT 웹 화면을 직접 읽고, 이전 답변을 바탕으로 다음 반박/질문을 생성하여 반자동 토론을 이어가는 코워크 구조.

## 핵심 조건
- API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만 사용
- 사용자는 ChatGPT에 로그인 상태 유지
- 완전 무인 자동화가 아닌 반자동 코워크 (사용자가 주제/방향 결정, Claude가 실행)
- 로그는 로컬 파일로 저장

## 사용자 개입 금지 + 실행 루프 (hooks 강제)

> stop_guard.sh가 금지 문구를 차단한다. prompt_inject.sh가 체크리스트를 주입한다.

사용자에게 중간 승인 요청 금지. 예외: 입력값 부족 / 비가역 실행 / 명시적 "검토만" 지시.

실행 루프: 방향 지시 → GPT 토론 → 합의 → 즉시 실행 → GPT 공유 → 추가수정 시 재공유 루프 → 루프 완료 후 사용자 보고 1회.

## 지정 채팅방 원칙 (필수)
- 반드시 지정된 프로젝트방만 사용한다
  - URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
  - 방 이름: `CLAUDE COWORK 업무 자동화 지침만들기`
- `chatgpt.com` 루트 또는 `/c/` 일반 대화창에 임의로 새 대화를 여는 것은 금지
- 새 대화가 필요한 경우에도 반드시 위 프로젝트 하위에서만 개설

### 채팅방 입장 규칙
- 프로젝트 페이지 진입 후 **채팅 목록의 첫 번째(최상단) 대화방**에 바로 입장한다
- 특정 대화를 지정받지 않는 한, 항상 첫 번째 방 = 최신 대화로 진입
- 기존 대화 URL을 별도 기억/하드코딩하지 않는다 — 매번 목록에서 첫 번째를 선택

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

### GPT 응답 비판적 분석 — 하네스 방식 (필수)

> stop_guard.sh가 채택/보류/버림 누락을 차단한다. prompt_inject.sh가 체크리스트를 주입한다.

GPT 응답 → 주장 2~4개 분해 → 라벨링 → 채택/보류/버림 판정 → 반박 생성.

라벨: 실증됨 / 일반론 / 환경 미스매치 / 과잉설계
판정: 채택(실증만) / 보류(일반론) / 버림(미스매치+과잉)

**필수 출력**: 반박문 첫 문단에 `채택:` `보류:` `버림:` 포함. 버림+보류 0건이면 재분해.
**환경 게이트**: 채택 후보는 (1)우리 환경 유지 (2)세션 지속성 불필요 (3)실증과 미충돌 통과 필수.

### 반박 생성 규칙
- 분해·판정 기반 반박 포인트 도출. 근거 + 대안 구조. 승인 없이 자동 전송.

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
| ChatGPT 응답 미완료 | 적응형 polling(5/10/15초), 최대 300초 timeout. 초과 시 사용자에게 보고 |
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
