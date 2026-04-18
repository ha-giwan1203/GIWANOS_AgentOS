# Gemini 채팅 전송

Gemini 웹 UI (gemini.google.com)에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
웹 UI 우선 사용 원칙: API 호출 금지, Chrome MCP 브라우저로만 조작한다.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 탭 확인 (재사용 우선)

1. `tabs_context_mcp(createIfEmpty=true)` → MCP 그룹 탭 목록 확인
2. `gemini.google.com` URL 포함 탭 있으면 → 해당 탭 재사용
3. 없으면 `.claude/state/gemini_chat_url` 읽기 → 새 탭(`tabs_create_mcp`) 생성 후 navigate

### 2. 채팅방 확인

- 현재 탭 URL이 `gemini.google.com/gem/` 포함 확인
- 포함되면 → 그대로 사용, `.claude/state/gemini_chat_url` 갱신
- 미포함이면 → `.claude/state/gemini_gem_url` 읽기 → navigate → 3초 대기

### 3. SEND GATE (생략 금지)

```javascript
// 전송 버튼 상태 확인 — aria-disabled=true 이면 아직 생성 중
const btn = document.querySelector('[aria-label="메시지 보내기"]');
btn ? btn.getAttribute('aria-disabled') : 'not_found';
```

- `"true"` → 현재 응답 생성 중 → `/gemini-read`로 먼저 완료 대기
- `"false"` → 전송 가능

### 4. 텍스트 입력 + 전송

```javascript
const ta = document.querySelector('.ql-editor');
ta.focus();
document.execCommand('insertText', false, TEXT);
setTimeout(() => {
  const btn = document.querySelector('[aria-label="메시지 보내기"]');
  if (btn && btn.getAttribute('aria-disabled') === 'false') btn.click();
}, 500);
'sent';
```

- `TEXT`에 `$ARGUMENTS` 삽입
- `javascript_tool` 한 번으로 입력+전송 완료
- fallback: `find`(query="메시지 보내기 버튼") → `computer`(left_click)
- `type` / `form_input` / CDP 금지

### 5. 응답 완료 대기

```javascript
// 전송 버튼 aria-disabled가 false로 돌아오면 완료
const btn = document.querySelector('[aria-label="메시지 보내기"]');
btn ? btn.getAttribute('aria-disabled') : 'not_found';
```

- 적응형 polling:
  - 0~20초: sleep 3
  - 20~60초: sleep 5
  - 60초~: sleep 8
  - 최대 300초
- `aria-disabled="false"` 반환 시 완료

### 6. 응답 읽기

```javascript
const blocks = document.querySelectorAll('model-response');
const last = blocks[blocks.length - 1];
last ? last.innerText : '';
```

- 응답 텍스트를 호출자에게 반환

## 에러 처리
- 탭 소실: `tabs_context_mcp(createIfEmpty=true)` → `.claude/state/gemini_chat_url`로 재진입
- `.ql-editor` 없음: 3초 대기 후 1회 재시도 → 실패 시 "Gemini 입력창 없음" 보고
- 전송 버튼 미발견: 1초 대기 후 1회 재시도
- 300초 타임아웃: "Gemini 응답 타임아웃" 보고 후 중단

## 주의사항
- [NEVER] Gemini API 호출 금지 — 웹 UI만 사용
- [NEVER] 새 Gem 생성 또는 새 채팅 개설 금지 — 기존 채팅방 재사용
- [MUST] 전송 본문 자연어는 한국어만
- [MUST] 탭 URL이 `gemini.google.com/gem/` 포함인지 매번 확인

## 고정 셀렉터 참조
```
입력창:    .ql-editor                        (contenteditable DIV)
전송버튼:  [aria-label="메시지 보내기"]       (BUTTON)
응답 노드: model-response                    (커스텀 엘리먼트)
완료 감지: [aria-label="메시지 보내기"] aria-disabled="false"
```
