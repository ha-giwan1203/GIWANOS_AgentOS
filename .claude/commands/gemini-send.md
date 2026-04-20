# Gemini 채팅 전송

Gemini 웹 UI (gemini.google.com)에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
웹 UI 우선 사용 원칙: API 호출 금지, Chrome MCP 브라우저로만 조작한다.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 채팅방 진입 (탭 재사용 우선 + 매 세션 최상단 대화방 재탐지)

> gpt-send 1-B와 동일 철학: 탭 상태 무관하게 **매 세션 Gem 최상단(최신) 대화방을 자동 재탐지**한다. 이전 세션의 `gemini_chat_url`을 검증 없이 재사용 금지.

**Gem URL 원본**: `.claude/state/gemini_gem_url` (고정값, 변경 시 이 파일만 수정)

#### 1-A. 기존 탭 복원 시도 (새 탭 생성 전 필수)
1. `tabs_context_mcp(createIfEmpty=true)` → MCP 그룹 탭 목록 확인
2. MCP 그룹 탭 중 `gemini.google.com` URL 포함 탭이 있으면 → 해당 탭 재사용 (1-B로)
3. 없으면 → `.claude/state/gemini_tab_id` 파일 읽기
   - 파일 존재 + 저장된 tabId가 MCP 그룹 탭 목록에 있음 → 해당 탭 재사용 (1-B로)
   - 파일 없음 or tabId가 목록에 없음 → **이때만** 새 탭 생성 (`tabs_create_mcp`)
4. 사용할 탭 ID 확정

#### 1-B. 대화방 진입 (매 세션 최상단 재탐지)

1. `.claude/state/gemini_gem_url` 읽기 → 해당 URL로 navigate → **1초 대기** (세션79 속도 개선). **fallback**: 1초 후 `.ql-editor` 또는 `recent-chat-list-item` 미탐지 시 **3초 추가 대기 1회** 재시도. 2회째 실패 시 "Gemini UI 로드 실패" 보고 (GPT A분류 제안 반영, 양측 PASS)
2. `javascript_tool`로 이 Gem의 **최상단 최근 대화방 href** 추출:
```javascript
// recent-chat-list-item = 이 Gem 전용 최근 대화 (최대 3개)
const recentItems = Array.from(document.querySelectorAll('recent-chat-list-item'));
const topTitle = recentItems.length > 0
  ? (recentItems[0].innerText || '').split('\n').map(s => s.trim()).filter(Boolean).pop()
  : null;
// sidebar all-conversations에서 동일 title 매칭 → href (/app/{conv_id}) 반환
let href = null;
if (topTitle) {
  const match = Array.from(document.querySelectorAll('a[data-test-id="conversation"]'))
    .find(a => (a.innerText || '').trim().includes(topTitle));
  href = match ? match.getAttribute('href') : null;
}
JSON.stringify({topTitle, href});
```
3. `href`가 `/app/{conv_id}` 형태면 → `https://gemini.google.com${href}` 로 navigate → **1초 대기** (세션79 속도 개선: 3초→1초)
4. 진입 성공 시 (URL이 `/app/` 또는 `/gem/{gem_id}/{conv_id}` 형태 확인 후):
   - `.claude/state/gemini_chat_url` 갱신 (최종 current URL)
   - `.claude/state/gemini_tab_id`에 현재 tabId 저장 (다음 세션 재사용용)
5. `recent-chat-list-item`이 0개인 경우 (이 Gem에 기존 대화 없음) → Gem 기본 URL(`/gem/{gem_id}`)에 머물고 새 대화 시작 상태로 진행. `gemini_chat_url`은 current URL로 갱신

- **[NEVER]** 이전 세션의 `gemini_chat_url` 값을 검증 없이 재사용 금지
- **[NEVER]** 탭 URL이 `/gem/` 또는 `/app/`으로 보여도 1-B 생략 금지 — 매 세션 Gem URL navigate + 최상단 재탐지 필수
- 같은 세션 2회차 이후 호출에서만 `gemini_chat_url` 캐시 허용

### 1-C. 대상 탭 활성화 (세션70 실증 — 백그라운드 throttling 대응, 생략 금지)

Chrome 백그라운드 탭 JS/네트워크 throttling 때문에 Gemini 탭이 포커스 없으면 응답 DOM 생성이 지연되거나 누락된다 (세션69 synthesis 미수령 원인). 전송 직전 대상 탭을 foreground로 강제 전환한다.

```
navigate(url=gemini_chat_url, tabId=gemini_tab_id)  # 동일 URL 재호출 → 탭 foreground 전환
```

- Chrome MCP는 tab activate API 미제공. `navigate` 재호출이 유일 회피 경로.
- 페이지 상태는 재로드 없이 유지됨.
- 3자 토론에서 GPT→Gemini 전환 시 특히 필수.
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 2. SEND GATE (생략 금지)

```javascript
// 전송 버튼 상태 확인 — aria-disabled=true 이면 아직 생성 중
const btn = document.querySelector('[aria-label="메시지 보내기"]');
btn ? btn.getAttribute('aria-disabled') : 'not_found';
```

- `"true"` → 현재 응답 생성 중 → `/gemini-read`로 먼저 완료 대기
- `"false"` → 전송 가능

### 3. 텍스트 입력 + 전송

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

### 4. 응답 완료 대기

```javascript
// 전송 버튼 aria-disabled가 false로 돌아오면 완료
const btn = document.querySelector('[aria-label="메시지 보내기"]');
btn ? btn.getAttribute('aria-disabled') : 'not_found';
```

- 적응형 polling (세션79 속도 개선):
  - 0~20초: sleep 2 (기존 3)
  - 20~60초: sleep 3 (기존 5)
  - 60초~: sleep 5 (기존 8)
  - 최대 300초
- `aria-disabled="false"` 반환 시 완료

### 5. 응답 읽기

```javascript
const blocks = document.querySelectorAll('model-response');
const last = blocks[blocks.length - 1];
last ? last.innerText : '';
```

- 응답 텍스트를 호출자에게 반환

## 에러 처리
- 탭 소실: `tabs_context_mcp(createIfEmpty=true)` → 새 탭 생성 후 1-B 재실행
- 최상단 대화 탐지 실패 (recent-chat-list-item 0개): Gem 기본 URL 머물고 새 대화로 진행
- 제목 매칭 실패 (recent title과 sidebar anchor가 일치 안 함): Gem 기본 URL 유지 + 사용자 보고
- `.ql-editor` 없음: 3초 대기 후 1회 재시도 → 실패 시 "Gemini 입력창 없음" 보고
- 전송 버튼 미발견: 1초 대기 후 1회 재시도
- 300초 타임아웃: "Gemini 응답 타임아웃" 보고 후 중단

## 주의사항
- [NEVER] Gemini API 호출 금지 — 웹 UI만 사용
- [NEVER] 새 Gem 생성 또는 임의 새 채팅 개설 금지 — 매 세션 최상단(최신) 대화방 자동 진입
- [NEVER] 이전 세션의 `gemini_chat_url`을 검증 없이 재사용 금지 (탭 URL 상태와 무관하게 1-B 재실행)
- [MUST] 전송 본문 자연어는 한국어만
- [MUST] 1-B 실행 결과 최종 URL로 `gemini_chat_url` 갱신

## 고정 셀렉터 참조
```
입력창:    .ql-editor                        (contenteditable DIV)
전송버튼:  [aria-label="메시지 보내기"]       (BUTTON)
응답 노드: model-response                    (커스텀 엘리먼트)
완료 감지: [aria-label="메시지 보내기"] aria-disabled="false"
```
