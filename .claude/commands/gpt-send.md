# GPT 채팅 전송 (chrome-devtools-mcp 기반)

GPT 프로젝트방에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
토론모드·share-result·finish 등에서 공통 호출한다.

**2026-04-24 세션105 마이그레이션**: claude-in-chrome → chrome-devtools-mcp.
CDP Chrome(포트 9222, 프로필 `C:\temp\chrome-cdp`) 기동 필수. 기본 프로필에서는 M136+ 보안으로 CDP 차단됨.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 채팅방 진입 (페이지 재사용 우선 + 매 세션 대화방 재탐지)

**프로젝트 URL:** `.claude/state/gpt_project_url` 파일에서 읽는다 (고정값, 변경 시 이 파일만 수정)

#### 1-Z. 세션 진입 캐시 체크 (D안 2026-04-20 — 진입 병목 감축)

`.claude/state/gpt_skill_entry.ok` 파일 존재 여부로 **현재 세션 내 1회차/2회차 이후** 판정.
세션 시작 시 `session_start_restore.sh`가 이 파일을 삭제하므로 존재 자체가 "현재 세션에서 1-A/1-B 완료됨" 증명.

- **존재 (2회차 이후)** → 빠른 경로:
  1. `.claude/state/gpt_tab_id` (= pageId 정수), `.claude/state/debate_chat_url` 읽기
  2. `mcp__chrome-devtools-mcp__list_pages` → 저장된 pageId가 현재 목록에 존재하고 URL이 chatgpt.com 이면 재사용
  3. 탭 존재 → **1-A/1-B 스킵 → 1-C로 직행** (foreground 활성화만)
  4. 탭 소실/URL 불일치 → `gpt_skill_entry.ok` 삭제 → 1-A부터 전체 수행 (fallback)
- **없음 (1회차)** → 기존 1-A/1-B/1-C 전체 수행 후 **1-D에서 `.ok` 기록**

> 기존 `[NEVER] 탭 URL이 올바르게 보여도 1-B 생략 금지`는 **세션 간** 재사용 방지용. 세션 내 2회차 스킵은 SessionStart 훅이 매 세션 `.ok`를 무효화하므로 "세션 간 재사용 금지"와 충돌하지 않는다. `feedback_gpt_send_1b_skip.md` 참조.

#### 1-A. 기존 페이지 복원 시도 (새 페이지 생성 전 필수)
1. `mcp__chrome-devtools-mcp__list_pages` → 현재 페이지 목록 확인
2. 목록 중 `chatgpt.com` URL 포함 페이지 있으면 → 해당 pageId 재사용 (1-B로)
3. 없으면 → `.claude/state/gpt_tab_id` 파일 읽기
   - 파일 존재 + 저장된 pageId가 목록에 있고 chatgpt.com URL → 재사용
   - 파일 없음 or pageId 불일치 → **이때만** 새 페이지 생성 (`mcp__chrome-devtools-mcp__new_page(url=<gpt_project_url>)`)
4. 사용할 pageId 확정

#### 1-B. 대화방 진입 (매 세션 재탐지)
1. `.claude/state/gpt_project_url` 읽기
2. `mcp__chrome-devtools-mcp__select_page(pageId, bringToFront=true)`
3. `mcp__chrome-devtools-mcp__navigate_page(type="url", url=<gpt_project_url>)` → **1초 대기** (세션79 속도 개선). **fallback**: 1초 후 `evaluate_script`로 `#prompt-textarea` 또는 `a[href*="/c/"]` 미탐지 시 **3초 추가 대기 1회** 재시도. 2회째 실패 시 "페이지 로드 실패" 보고
4. `mcp__chrome-devtools-mcp__evaluate_script`로 최상단 **프로젝트** 채팅방 URL 추출:
```javascript
() => {
  const base = window.location.pathname.split('/project')[0];
  const links = document.querySelectorAll(`a[href*="${base}/c/"]`);
  return links.length > 0 ? links[0].href : null;
}
```
5. 반환된 URL로 `navigate_page(type="url", url=<href>)`
   - `base`는 프로젝트 slug 경로 (`/g/g-p-...`). 사이드바 일반 채팅(`/c/` 단독)은 자동 제외됨
6. 진입 성공 시 (URL에 프로젝트 slug 포함 확인 후):
   - `.claude/state/debate_chat_url` 갱신
   - `.claude/state/gpt_tab_id`에 현재 pageId 저장 (다음 세션 재사용용)
   - URL에 프로젝트 slug 미포함 시 → "프로젝트 대화방 탐지 실패" 에러 반환, 저장하지 않음

- **[NEVER]** 이전 세션의 debate_chat_url 값을 검증 없이 재사용 금지
- **[NEVER]** 매 세션 1-B 최소 1회 수행 금지 해제 금지 — 세션당 첫 호출은 반드시 navigate_page + 재탐지
- 같은 세션 내 2회차 이후 호출은 1-Z 빠른 경로로 1-A/1-B 스킵 (D안 2026-04-20)

### 1-C. 대상 페이지 활성화 (세션105 마이그레이션 — chrome-devtools-mcp 네이티브)

Chrome 백그라운드 탭 throttling 회피. 기존에는 `navigate` 재호출로 우회했으나, chrome-devtools-mcp의 `select_page(bringToFront=true)`가 CDP `Target.activateTarget`을 직접 호출해 정식 해결.

```
mcp__chrome-devtools-mcp__select_page(pageId=<gpt_page_id>, bringToFront=true)
```

- URL 재진입 불필요 — 탭 포커스 전환만 수행
- 3자 토론에서 GPT↔Gemini 전환 시 특히 필수
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 1-D. 진입 캐시 기록 (D안 2026-04-20 — 1회차 완료 시만)

1회차(`.ok` 없을 때)에 1-A/1-B/1-C를 모두 성공한 직후 `.claude/state/gpt_skill_entry.ok` 빈 파일 생성.

```bash
touch .claude/state/gpt_skill_entry.ok
```

2회차 이후 fast-path 실패(탭 소실 등)로 fallback 경로 타게 될 때 1-A/1-B/1-C 재수행 후 `.ok`를 **덮어쓰기(touch)**로 갱신.

### 2. SEND GATE (생략 금지)
- `mcp__chrome-devtools-mcp__evaluate_script`로 현재 대화 상태 읽기:
```javascript
() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = blocks.length ? blocks[blocks.length - 1] : null;
  return {
    count: blocks.length,
    lastLen: last ? (last.innerText || '').trim().length : 0,
    stopBtn: document.querySelector('[data-testid="stop-button"]') !== null
  };
}
```
- `stopBtn=true` 또는 마지막 블록 아직 성장 중이면 → `/gpt-read`로 먼저 완료 대기

### 3. 텍스트 입력 + 전송 (한 번에)

`mcp__chrome-devtools-mcp__evaluate_script`로 execCommand insertText:

```javascript
(text) => {
  const ta = document.querySelector('#prompt-textarea');
  if (!ta) return 'no_textarea';
  ta.focus();
  document.execCommand('insertText', false, text);
  setTimeout(() => {
    const btn = document.querySelector('[data-testid="send-button"]') ||
                document.querySelector('#composer-submit-button');
    if (btn) btn.click();
  }, 500);
  return 'sent';
}
```

- `evaluate_script(function=<위 코드>, args=[text])` 한 번으로 입력+전송 완료
- send-button 미발견 시 fallback: `take_snapshot` → 버튼 uid 확인 → `click(uid)`
- `fill` tool은 contenteditable div에서 불안정 → execCommand 우선

### 4. 응답 완료 대기
- 적응형 polling (세션79 속도 개선 + 세션83 thinking 확장):
  - thinking·reasoning 모델 감지는 `/gpt-read` 2-a 참조 (data-message-model-slug includes 판정)
  - 일반 모델: 2/3/5초 단계, 최대 300초
  - 확장추론 모델(isExtended=true): 2/3/5/8초 반복, 300초 이후 15/30초 단계, 최대 600초
- `evaluate_script`로 stop-button + 마지막 블록 상태 병행 확인:
```javascript
() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = blocks.length ? blocks[blocks.length - 1] : null;
  const slug = (last && last.getAttribute('data-message-model-slug') || '').toLowerCase();
  return {
    stopBtn: document.querySelector('[data-testid="stop-button"]') !== null,
    isExtended: slug.includes('thinking') || slug.includes('reasoning'),
    lastLen: last ? (last.innerText || '').trim().length : 0
  };
}
```
- 완료 판정: `stopBtn=false` 경로 또는 블록 안정 3회 연속 동일 (세션83, thinking 응답 중 stop-button 잔존 대비)

### 5. 응답 읽기

```javascript
() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = blocks[blocks.length - 1];
  return last ? last.innerText : '';
}
```

- 응답 텍스트를 사용자/호출자에게 반환

## 에러 처리
- 페이지 소실: `list_pages` 재조회 → 없으면 `new_page(url)` 재시도
- 전송 버튼 미발견: 1초 대기 후 1회 재시도 → `take_snapshot` + `click(uid)` fallback
- 300초 타임아웃: "GPT 응답 타임아웃" 보고 후 중단

## 주의사항
- 전송 본문 자연어는 한국어만
- 프로젝트방 외 대화 금지
- 매 세션 debate_chat_url 새로 탐지 (이전 값 재사용 금지)
- CDP Chrome(포트 9222) 미기동 시 즉시 실패 보고 — 기본 Chrome에서는 동작 불가

## 변경 이력
- 세션105 (2026-04-24): claude-in-chrome → chrome-devtools-mcp 전면 마이그레이션
  - `tabs_context_mcp` → `list_pages`
  - `tabs_create_mcp` → `new_page`
  - `navigate(url, tabId)` 재호출 탭 활성화 hack → `select_page(pageId, bringToFront=true)` CDP 네이티브
  - `javascript_tool` → `evaluate_script`
  - `get_page_text`/`find`/`computer` → `take_snapshot`/`click`/`fill` (필요 시만)
  - 상태 파일 `gpt_tab_id` 내용 의미 변경: claude-in-chrome tabId(문자열) → chrome-devtools-mcp pageId(정수)
