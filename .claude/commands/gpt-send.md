# GPT 채팅 전송

GPT 프로젝트방에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
토론모드·share-result·finish 등에서 공통 호출한다.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 채팅방 진입
1. `tabs_context_mcp` → 기존 ChatGPT 탭 확인
2. chatgpt.com 탭이 MCP 그룹에 있으면 해당 탭 사용, 없으면 새 탭 생성
3. `.claude/state/debate_chat_url` 읽기 → URL이 있고 프로젝트 slug 포함이면 직접 navigate
4. debate_chat_url 없으면: 프로젝트 URL navigate → `javascript_tool`로 URL 추출 → navigate
```javascript
const main = document.querySelector('main');
const links = main ? main.querySelectorAll('a[href*="/c/"]') : [];
links.length > 0 ? links[0].href : null;
```
5. 진입 성공 시 `.claude/state/debate_chat_url` 갱신

### 2. SEND GATE (생략 금지)
- `get_page_text`로 현재 대화 상태 읽기
- `[data-message-author-role="assistant"]` 마지막 블록 확인 → 미확인 응답 있으면 먼저 읽기

### 3. 텍스트 입력
```javascript
const ta = document.querySelector('#prompt-textarea');
ta.focus();
document.execCommand('insertText', false, text);
```
- `javascript_tool`로 위 코드 실행. `text`는 전달받은 메시지.
- `type` / `form_input` / CDP 금지

### 4. 전송
- `find`(query="send button") → ref 획득
- `computer`(action="left_click", ref=<ref>) → 전송 클릭

### 5. 응답 완료 대기
- 적응형 polling:
  - 0~20초: sleep 3
  - 20~60초: sleep 5
  - 60초~: sleep 8
  - 최대 300초
- `javascript_tool`로 `document.querySelector('[data-testid="stop-button"]') !== null` 확인
- false가 되면 완료

### 6. 응답 읽기
```javascript
const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
const last = blocks[blocks.length - 1];
last ? last.innerText : '';
```
- 응답 텍스트를 사용자/호출자에게 반환

## 에러 처리
- 탭 소실: `tabs_context_mcp`(createIfEmpty=true) 후 재시도
- 전송 버튼 미발견: 1초 대기 후 1회 재시도
- 300초 타임아웃: "GPT 응답 타임아웃" 보고 후 중단

## 주의사항
- 전송 본문 자연어는 한국어만
- 프로젝트방 외 대화 금지
- 매 세션 debate_chat_url 새로 탐지 (이전 값 재사용 금지)
