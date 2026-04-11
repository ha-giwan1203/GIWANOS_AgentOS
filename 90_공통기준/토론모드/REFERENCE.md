# 토론모드 상세 참조 (REFERENCE)

> CLAUDE.md에서 분리된 상세 배경·fallback·실험 규칙.
> 코어 규칙은 ENTRY.md(Primary) + CLAUDE.md(코어) 참조.
> 저수준 입력/DOM 처리 기술 상세는 `debate-mode/REFERENCE.md`를 기준으로 본다.

## 채팅방 입장 상세

### 탭 재사용 (신규 탭 중복 방지)
새 Claude 세션 시작 시 브라우저 탭을 먼저 확인한다.

```
0. .claude/state/debate_chat_url 읽기 → URL이 있으면 이것을 우선 사용
1. tabs_context_mcp → 현재 열린 탭 목록 확인
2. chatgpt.com 탭 매칭 우선순위:
   1순위: /g/g-p-69bca.../c/ 패턴 (프로젝트 내 대화) — debate_chat_url과 일치하면 switch
   2순위: /g/g-p-69bca... 패턴 (프로젝트 메인) — switch 후 대화 URL 추출
   기타 chatgpt.com 탭은 무시
3. 탭에 없으면 → debate_chat_url로 navigate (새 탭 불필요)
4. debate_chat_url도 없으면 → 프로젝트 URL 진입 후 아래 '대화 URL 추출' 절차 실행
5. 대화방 진입 성공 시 → .claude/state/debate_chat_url 갱신
```

### 대화 URL 추출 (클릭 대신 JS 직접 추출 — 2026-04-01 실증)

프로젝트 페이지에서 대화 목록 클릭은 React 이벤트 미트리거로 실패할 수 있다.
**클릭 시도 금지. 반드시 JS로 URL을 추출한 뒤 navigate()로 진입한다.**

```javascript
const main = document.querySelector('main');
const links = main ? main.querySelectorAll('a[href*="/c/"]') : [];
const url = links.length > 0 ? links[0].href : null;
url;  // → navigate()에 전달
```

> **주의 (2026-04-01 실증)**: `nav a[href*="/c/"]`는 사이드바 일반 대화 목록이다.
> 프로젝트 전용 대화는 `main` 영역 안에만 있고, URL에 `/g/g-p-.../c/...` 패턴을 포함한다.

```
실행 순서:
1. navigate → 프로젝트 URL (채팅 목록 페이지)
2. javascript_tool → 위 스크립트로 첫 번째 대화 URL 추출
3. navigate → 추출된 URL로 대화방 진입
```

## 입력+전송 상세

### 기본 전송 경로 (`cdp_chat_send.py`)

쉘이나 로컬 CDP 경로에서는 아래 helper를 기본 전송 경로로 사용한다.

```bash
python '.claude/scripts/cdp/cdp_chat_send.py' \
  --match-url '<chat_url>' \
  --text-file '<utf8_text_file>' \
  --mark-send-gate
```

- `--mark-send-gate`: assistant 최신 읽기 직후 `.claude/state/send_gate_passed` 갱신
- submit selector는 내부에서 `[data-testid="send-button"], #composer-submit-button` fallback 사용
- 토론모드 문서상 기본 전송 경로는 이것이며, 직접 DOM 조작은 helper를 쓸 수 없을 때만 예비 경로로 사용한다.

### 예비 경로: 통합 JS (1회 호출)
```javascript
const el = document.querySelector('#prompt-textarea');
el.focus();
document.execCommand('insertText', false, text);
setTimeout(() => {
  const btn = document.querySelector('[data-testid="send-button"], #composer-submit-button');
  if (btn && !btn.disabled) btn.click();
}, 100);
```

빈 입력창에서는 `composer-speech-button`만 보일 수 있으므로, 실제 submit button 재확인은 항상 `insertText` 이후에 다시 수행한다.

### 토론방 언어 규칙
- 토론방에 보내는 자연어 본문은 한국어만 사용한다.
- 판정 요청 라벨도 `통과 / 조건부 통과 / 실패`만 사용한다.
- 예외: code block, selector/data-testid, 파일 경로, commit SHA, 에러 원문 최소 인용
- 에러 원문 최소 인용은 `오류 원문:` 또는 `에러 원문:` 라벨 한 줄로만 허용한다.

### 예비 경로 2차 fallback (execCommand 실패 시)
```
textContent 직접 삽입 + new InputEvent('input', {bubbles:true, composed:true}) dispatch
```

## 응답 완료 감지 상세

```
방식:    stop-button 유무 확인 (polling)
완료:    document.querySelector('[data-testid="stop-button"]') === null

적응형 간격 (3단, 단축됨):
  0~20초:   sleep 3  (일반 응답 빠르게 캐치)
  20~60초:  sleep 5  (중간 구간)
  60초~:    sleep 8  (확장추론 대응)
timeout:    최대 300초 (확장추론 5분 대응)

매 polling 주기 구조:
  1. sleep N (적응형 간격)
  2. [사용자 중단 확인] sleep 복귀 후 사용자 메시지 유무 우선 확인
     "중단", "방향 바꿔", "멈춰" 등 → 즉시 polling 종료 + 현재 상태 보고
  3. javascript_tool → stop-button 유무 확인
  4. 조건 판정 (계속/완료/timeout)
```
> CDP 45초 timeout 때문에 javascript_tool 안에서 setInterval/Promise 기반 polling 불가.
> 반드시 `javascript_tool` + `sleep N` 분리 호출로 루프를 구성한다.

## 최신 응답 읽기 상세

```javascript
const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
const last = msgs[msgs.length - 1];
last ? last.innerText : 'NO_MSG';
```

### fallback 순서
1. javascript_tool로 마지막 assistant 노드 직접 추출
2. 텍스트가 너무 길거나 잘리면 get_page_text로 전체 페이지 텍스트 추출 후 파싱
3. 파싱 실패 시 read_page로 DOM 구조에서 마지막 메시지 요소 탐색

## SEND GATE 상세

```javascript
const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
const lastText = msgs[msgs.length - 1]?.innerText?.slice(0, 100) || '';
const stopBtn = document.querySelector('[data-testid="stop-button"]');
JSON.stringify({lastSnippet: lastText, isGenerating: !!stopBtn});
```

1. 마지막 assistant 블록 텍스트 100자를 읽는다
2. GPT가 아직 생성 중(stop-button 존재)이면 → 대기
3. 이전에 읽은 내용과 다르면 → 새 응답 전체 읽기 → 하네스 재계산 → 반박문 재작성 후 전송
4. 같으면 → 변동 없음 → 예정대로 전송 진행
5. helper는 `--mark-send-gate` 시 gate 파일을 갱신하고 전송을 진행한다
6. 직접 자바스크립트 예비 경로에서는 gate 파일이 없거나 120초 초과 시 `send_gate.sh` 훅이 차단

## GPT 대기 중 병행 작업

> GPT 응답 대기(30~60초) 동안 background Agent로 독립 작업을 병행할 수 있다.
> Agent 도구는 독립 컨텍스트에서 실행되므로 세션 충돌 없음 (GPT 합의 2026-04-02).
> 단, 동일 대상 파일·로그·출력물 동시 수정은 금지.

## 하네스 분석 상세

라벨: 실증됨 / 일반론 / 환경 미스매치 / 과잉설계
판정: 채택(실증만) / 보류(일반론) / 버림(미스매치+과잉)
환경 게이트: 채택 후보는 (1)우리 환경 유지 (2)세션 지속성 불필요 (3)실증과 미충돌 통과 필수

### 사용자 보고 축약
- 매턴 표 대신 1줄 요약: `채택 N건 / 보류 N건 / 버림 N건 — [핵심 판정 이유 1줄]`
- 상세 분해·라벨링은 반박문(GPT에 전송하는 텍스트) 안에만 포함

## 로그 저장 구조

```
logs/
├── debate_YYYYMMDD_HHMMSS.md
└── debate_YYYYMMDD_HHMMSS.json
```

## Selector Smoke Test (토론 시작 시 필수)

토론모드 Step 1 완료 직후, 메시지 전송 전에 composer/응답 영역 selector를 검증한다.
빈 입력창 상태에서는 `send-button` 대신 `composer-speech-button`만 보일 수 있으므로 이를 정상으로 간주한다.
하나라도 실패하면 토론 진행을 중단하고 사용자에게 보고한다.

```javascript
const selectors = {
  promptTextarea: '#prompt-textarea',
  sendButton: '[data-testid="send-button"]',
  submitButtonById: '#composer-submit-button',
  composerSpeechButton: '[data-testid="composer-speech-button"]',
  stopButton: '[data-testid="stop-button"]',  // 생성 중이 아니면 null 허용
  assistantMsg: '[data-message-author-role="assistant"]'
};
const results = {};
for (const [name, sel] of Object.entries(selectors)) {
  results[name] = !!document.querySelector(sel);
}
// stopButton은 생성 중이 아니면 false 허용
// 빈 composer에서는 sendButton이 없고 composerSpeechButton만 있을 수 있음
const required = ['promptTextarea', 'assistantMsg'];
const missing = required.filter(k => !results[k]);
if (!(results.sendButton || results.submitButtonById || results.composerSpeechButton)) {
  missing.push('composerAction');
}
JSON.stringify({
  results,
  missing,
  pass: missing.length === 0,
  note: (results.sendButton || results.submitButtonById)
    ? 'send ready'
    : 'idle composer; send button appears after text insert'
});
```

전송 직전에는 아래 추가 확인을 한 번 더 수행한다.

```javascript
const hasSubmit = !!document.querySelector('[data-testid="send-button"], #composer-submit-button');
JSON.stringify({hasSubmit});
```

| 결과 | 행동 |
|------|------|
| pass: true | 정상 진행 |
| missing 있음 | 토론 중단 → 사용자에게 "ChatGPT UI 변경 감지: {missing} selector 없음" 보고 |

> ChatGPT UI 업데이트로 selector가 변경되면 REFERENCE.md의 selector 목록과 이 테스트를 함께 갱신한다.

---

## 오류 대응

| 상황 | 대응 |
|------|------|
| ChatGPT 응답 미완료 | 적응형 polling(3/5/8초), 최대 300초 timeout. 초과 시 사용자에게 보고 |
| 텍스트 추출 실패 | javascript_tool → get_page_text → read_page 순서로 fallback |
| 로그인 만료 | 사용자에게 재로그인 요청 |
| 네트워크 오류 | 로그 기록 후 중단 |
