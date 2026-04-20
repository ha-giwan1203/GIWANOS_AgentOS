# GPT 채팅 전송

GPT 프로젝트방에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
토론모드·share-result·finish 등에서 공통 호출한다.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 채팅방 진입 (탭 재사용 우선 + 매 세션 대화방 재탐지)

**프로젝트 URL:** `.claude/state/gpt_project_url` 파일에서 읽는다 (고정값, 변경 시 이 파일만 수정)

#### 1-A. 기존 탭 복원 시도 (새 탭 생성 전 필수)
1. `tabs_context_mcp(createIfEmpty=true)` → MCP 그룹 탭 목록 확인
2. MCP 그룹 탭 중 chatgpt.com URL 포함 탭이 있으면 → 해당 탭 재사용 (1-B로)
3. 없으면 → `.claude/state/gpt_tab_id` 파일 읽기
   - 파일 존재 + 저장된 tabId가 MCP 그룹 탭 목록에 있음 → 해당 탭 재사용 (1-B로)
   - 파일 없음 or tabId가 목록에 없음 → **이때만** 새 탭 생성 (`tabs_create_mcp`)
4. 사용할 탭 ID 확정

#### 1-B. 대화방 진입 (매 세션 재탐지)
1. `.claude/state/gpt_project_url` 읽기 → 해당 URL로 navigate → **1초 대기** (세션79 속도 개선). **fallback**: 1초 후 `#prompt-textarea` 또는 `a[href*="/c/"]` 미탐지 시 **3초 추가 대기 1회** 재시도. 2회째 실패 시 "페이지 로드 실패" 보고 (GPT A분류 제안 반영, 양측 PASS)
2. `javascript_tool`로 최상단 **프로젝트** 채팅방 URL 추출 → navigate
```javascript
const base = window.location.pathname.split('/project')[0];
const links = document.querySelectorAll(`a[href*="${base}/c/"]`);
links.length > 0 ? links[0].href : null;
```
   - `base`는 프로젝트 slug 경로 (`/g/g-p-...`). 사이드바 일반 채팅(`/c/` 단독)은 자동 제외됨
3. 진입 성공 시 (URL에 프로젝트 slug 포함 확인 후):
   - `.claude/state/debate_chat_url` 갱신
   - `.claude/state/gpt_tab_id`에 현재 tabId 저장 (다음 세션 재사용용)
   - URL에 프로젝트 slug 미포함 시 → "프로젝트 대화방 탐지 실패" 에러 반환, 저장하지 않음

- **[NEVER]** 이전 세션의 debate_chat_url 값을 검증 없이 재사용 금지
- **[NEVER]** 탭 URL이 올바르게 보여도 1-B 생략 금지 — 탭 상태와 무관하게 매 세션 navigate + 재탐지 필수
- 같은 세션 내 2회차 이후 호출에서만 debate_chat_url 캐시 허용

### 1-C. 대상 탭 활성화 (세션70 실증 — 백그라운드 throttling 대응, 생략 금지)

Chrome 백그라운드 탭 JS/네트워크 throttling으로 전송 후 응답 DOM이 생성되지 않는 실증 사례(세션69) 있음. 전송 직전 대상 탭을 foreground로 강제 전환한다.

```
navigate(url=debate_chat_url, tabId=gpt_tab_id)  # 동일 URL 재호출 → 탭 foreground 전환
```

- Chrome MCP는 별도 activate API 없음. `navigate` 재호출이 유일 회피 경로.
- 같은 URL이어도 반드시 재호출. 페이지 상태는 보존됨.
- 3자 토론에서 GPT→Gemini 또는 Gemini→GPT 전환 시 특히 필수.
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 2. SEND GATE (생략 금지)
- `get_page_text`로 현재 대화 상태 읽기
- `[data-message-author-role="assistant"]` 마지막 블록 확인 → 미확인 응답 있으면 먼저 읽기

### 3. 텍스트 입력 + 전송 (한 번에)
```javascript
const ta = document.querySelector('#prompt-textarea');
ta.focus();
document.execCommand('insertText', false, text);
setTimeout(() => {
  const btn = document.querySelector('[data-testid="send-button"]');
  if (btn) btn.click();
}, 500);
'sent';
```
- `javascript_tool` 한 번으로 입력+전송 완료
- send-button testid가 없으면 fallback: `find`(query="send button") → `computer`(left_click)
- `type` / `form_input` / CDP 금지

### 4. 응답 완료 대기
- 적응형 polling (세션79 속도 개선 + 세션83 thinking 확장):
  - thinking·reasoning 모델 감지는 `/gpt-read` 2-a 참조 (data-message-model-slug includes 판정)
  - 일반 모델: 2/3/5초 단계, 최대 300초
  - 확장추론 모델(isExtended=true): 2/3/5/8초 반복, 300초 이후 15/30초 단계, 최대 600초
- `javascript_tool`로 stop-button + 마지막 블록 상태 병행 확인 (stop-button 단독 판정 금지):
  ```javascript
  (() => {
    const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
    const last = blocks.length ? blocks[blocks.length - 1] : null;
    const slug = (last && last.getAttribute('data-message-model-slug') || '').toLowerCase();
    return JSON.stringify({
      stopBtn: document.querySelector('[data-testid="stop-button"]') !== null,
      isExtended: slug.includes('thinking') || slug.includes('reasoning'),
      lastLen: last ? (last.innerText || '').trim().length : 0
    });
  })();
  ```
- 완료 판정: `stopBtn=false` 경로 또는 블록 안정 3회 연속 동일 (세션83, thinking 응답 중 stop-button 잔존 대비)

### 5. 응답 읽기
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
