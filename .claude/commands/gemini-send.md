# Gemini 채팅 전송 (chrome-devtools-mcp 기반)

Gemini 웹 UI (gemini.google.com)에 메시지를 입력하고 전송한 뒤 응답을 읽어오는 단일 명령.
웹 UI 우선 사용 원칙: API 호출 금지, chrome-devtools-mcp로만 조작한다.

**2026-04-24 세션105 마이그레이션**: claude-in-chrome → chrome-devtools-mcp.
CDP Chrome(포트 9222, 프로필 `C:\temp\chrome-cdp`) 기동 필수.

**2026-04-25 세션107 정책 강화 (사용자 지시)**: CDP Chrome 단독 사용. 일반 Chrome 프로필 / claude-in-chrome 계열 MCP 호출 금지. CDP 미기동 시 즉시 실패 보고.

## 인자
- `$ARGUMENTS`: 전송할 메시지 텍스트 (필수)

## 실행 순서

### 1. 채팅방 진입 (페이지 재사용 우선 + 매 세션 최상단 대화방 재탐지)

> gpt-send 1-B와 동일 철학: 탭 상태 무관하게 **매 세션 Gem 최상단(최신) 대화방을 자동 재탐지**한다.

**Gem URL 원본**: `.claude/state/gemini_gem_url` (고정값, 변경 시 이 파일만 수정)

#### 1-Z. 세션 진입 캐시 체크 (D안 2026-04-20 — 진입 병목 감축)

`.claude/state/gemini_skill_entry.ok` 파일 존재 여부로 현재 세션 내 1회차/2회차 이후 판정.

- **존재 (2회차 이후)** → 빠른 경로:
  1. `.claude/state/gemini_tab_id` (= pageId 정수), `.claude/state/gemini_chat_url` 읽기
  2. `mcp__chrome-devtools-mcp__list_pages` → 저장된 pageId가 gemini.google.com URL로 존재하는지 확인
  3. 존재 → **1-A/1-B 스킵 → 1-C로 직행** (foreground 활성화만)
  4. 소실/URL 불일치 → `gemini_skill_entry.ok` 삭제 → 1-A부터 전체 수행 (fallback)
- **없음 (1회차)** → 기존 1-A/1-B/1-C 전체 수행 후 **1-D에서 `.ok` 기록**

#### 1-A. 기존 페이지 복원 시도 (새 페이지 생성 전 필수)
1. `mcp__chrome-devtools-mcp__list_pages` → 페이지 목록 확인
2. 목록 중 `gemini.google.com` URL 포함 페이지 있으면 → 해당 pageId 재사용 (1-B로)
3. 없으면 → `.claude/state/gemini_tab_id` 파일 읽기
   - 파일 존재 + 저장된 pageId가 목록에 있고 gemini.google.com URL → 재사용
   - 파일 없음 or pageId 불일치 → **이때만** `new_page(url=<gemini_gem_url>)` 생성
4. 사용할 pageId 확정

#### 1-B. 대화방 진입 (매 세션 최상단 재탐지)

1. `.claude/state/gemini_gem_url` 읽기
2. `mcp__chrome-devtools-mcp__select_page(pageId, bringToFront=true)`
3. `mcp__chrome-devtools-mcp__navigate_page(type="url", url=<gemini_gem_url>)` → **1초 대기**. fallback: 3초 추가 대기 1회 재시도. 2회째 실패 시 "Gemini UI 로드 실패" 보고
4. `mcp__chrome-devtools-mcp__evaluate_script`로 이 Gem의 **최상단 최근 대화방 href** 추출:
```javascript
() => {
  const recentItems = Array.from(document.querySelectorAll('recent-chat-list-item'));
  const topTitle = recentItems.length > 0
    ? (recentItems[0].innerText || '').split('\n').map(s => s.trim()).filter(Boolean).pop()
    : null;
  let href = null;
  if (topTitle) {
    const match = Array.from(document.querySelectorAll('a[data-test-id="conversation"]'))
      .find(a => (a.innerText || '').trim().includes(topTitle));
    href = match ? match.getAttribute('href') : null;
  }
  return { topTitle, href };
}
```
5. `href`가 `/app/{conv_id}` 또는 `/gem/{gem_id}/{conv_id}` 형태면 → `navigate_page(type="url", url=<https://gemini.google.com${href}>)` → **1초 대기**
6. 진입 성공 시 (URL 형태 확인 후):
   - `.claude/state/gemini_chat_url` 갱신 (최종 current URL)
   - `.claude/state/gemini_tab_id`에 현재 pageId 저장
7. `recent-chat-list-item`이 0개인 경우 → Gem 기본 URL에 머물고 새 대화 시작 상태로 진행. `gemini_chat_url`은 current URL로 갱신

- **[NEVER]** 이전 세션의 `gemini_chat_url` 값을 검증 없이 재사용 금지
- **[NEVER]** 매 세션 1-B 최소 1회 수행 금지 해제 금지
- 같은 세션 2회차 이후 호출은 1-Z 빠른 경로로 1-A/1-B 스킵

#### 1-B-1. 모델 설정 확인/선택 (세션105 Round 2 실증 — 생략 금지)

**증상**: Gemini Gem 채팅방은 입장할 때마다 **모델 설정이 고정되지 않는다**. 기본값이 적용되거나 이전 선택이 풀려 있을 수 있어, 전송 전 매번 수동으로 모델을 선택해야 일관된 응답 품질이 보장된다. 세션105 Round 2 진행 중 사용자 지적으로 확인됨.

**대응 (SEND GATE 전 필수)**:
1. `evaluate_script`로 현재 선택된 모델 라벨 확인:
```javascript
() => {
  // 모델 선택 버튼은 상단 toolbar 또는 composer 근처
  const btn = document.querySelector('[data-test-id="bard-mode-menu-button"]') ||
              document.querySelector('button[aria-label*="모델"]') ||
              document.querySelector('button[jsname][aria-haspopup="menu"]');
  return btn ? {label: btn.innerText.trim(), html: btn.outerHTML.slice(0, 300)} : null;
}
```
2. 원하는 모델(기본: Pro/2.5 Pro 계열)과 다르면:
   - `take_snapshot` → 모델 선택 버튼 uid 확인
   - `click(uid)` → 드롭다운 열기
   - `take_snapshot` → 대상 모델 옵션 uid 확인
   - `click(uid)` → 모델 선택 확정
3. 모델 설정 실패 시 "Gemini 모델 설정 실패 — 사용자 수동 선택 필요" 보고

**[NEVER]**:
- 모델 설정 단계 생략 금지 — 기본값 응답 품질이 토론에 부적합할 수 있음
- 이전 세션의 모델 선택 상태를 재사용 금지 (Gem 채팅방 재진입 시 풀리는 증상)

### 1-C. 대상 페이지 활성화 (세션105 마이그레이션 — CDP 네이티브)

Chrome 백그라운드 탭 throttling 회피. chrome-devtools-mcp의 `select_page(bringToFront=true)`가 CDP `Target.activateTarget` 직접 호출로 정식 해결.

```
mcp__chrome-devtools-mcp__select_page(pageId=<gemini_page_id>, bringToFront=true)
```

- URL 재진입 불필요 — 탭 포커스 전환만
- 3자 토론에서 GPT→Gemini 전환 시 특히 필수
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 1-D. 진입 캐시 기록 (D안 2026-04-20 — 1회차 완료 시만)

```bash
touch .claude/state/gemini_skill_entry.ok
```

### 2. SEND GATE (생략 금지)

`mcp__chrome-devtools-mcp__evaluate_script`:
```javascript
() => {
  const btn = document.querySelector('[aria-label="메시지 보내기"]');
  return btn ? btn.getAttribute('aria-disabled') : 'not_found';
}
```

- `"true"` → 현재 응답 생성 중 → `/gemini-read`로 먼저 완료 대기
- `"false"` → 전송 가능

### 3. 텍스트 입력 + 전송

`mcp__chrome-devtools-mcp__evaluate_script`:
```javascript
(text) => {
  const ta = document.querySelector('.ql-editor');
  if (!ta) return 'no_editor';
  ta.focus();
  document.execCommand('insertText', false, text);
  setTimeout(() => {
    const btn = document.querySelector('[aria-label="메시지 보내기"]');
    if (btn && btn.getAttribute('aria-disabled') === 'false') btn.click();
  }, 500);
  return 'sent';
}
```

- `evaluate_script(function=<위>, args=[text])` 한 번으로 입력+전송 완료
- fallback: `take_snapshot` → "메시지 보내기" 버튼 uid 확인 → `click(uid)`
- `fill` tool은 contenteditable div에서 불안정 → execCommand 우선

### 4. 응답 완료 대기

```javascript
() => {
  const btn = document.querySelector('[aria-label="메시지 보내기"]');
  return btn ? btn.getAttribute('aria-disabled') : 'not_found';
}
```

- 적응형 polling:
  - 0~20초: sleep 2
  - 20~60초: sleep 3
  - 60초~: sleep 5
  - 최대 300초
- `aria-disabled="false"` 반환 시 완료

### 5. 응답 읽기

```javascript
() => {
  const blocks = document.querySelectorAll('model-response');
  const last = blocks[blocks.length - 1];
  return last ? last.innerText : '';
}
```

- 응답 텍스트를 호출자에게 반환

## 에러 처리
- 페이지 소실: `list_pages` 재조회 → 없으면 `new_page(url=<gemini_gem_url>)` 재시도
- 최상단 대화 탐지 실패 (recent-chat-list-item 0개): Gem 기본 URL 머물고 새 대화로 진행
- 제목 매칭 실패: Gem 기본 URL 유지 + 사용자 보고
- `.ql-editor` 없음: 3초 대기 후 1회 재시도 → 실패 시 "Gemini 입력창 없음" 보고
- 전송 버튼 미발견: 1초 대기 후 1회 재시도
- 300초 타임아웃: "Gemini 응답 타임아웃" 보고 후 중단

## 주의사항
- [NEVER] Gemini API 호출 금지 — 웹 UI만 사용
- [NEVER] 새 Gem 생성 또는 임의 새 채팅 개설 금지
- [NEVER] 이전 세션의 `gemini_chat_url`을 검증 없이 재사용 금지
- [MUST] 전송 본문 자연어는 한국어만
- [MUST] 1-B 실행 결과 최종 URL로 `gemini_chat_url` 갱신
- CDP Chrome(포트 9222) 미기동 시 즉시 실패 보고

## 고정 셀렉터 참조
```
입력창:    .ql-editor                        (contenteditable DIV)
전송버튼:  [aria-label="메시지 보내기"]       (BUTTON)
응답 노드: model-response                    (커스텀 엘리먼트)
완료 감지: [aria-label="메시지 보내기"] aria-disabled="false"
```

## 변경 이력
- 세션105 (2026-04-24): claude-in-chrome → chrome-devtools-mcp 전면 마이그레이션
  - `tabs_context_mcp` → `list_pages`
  - `tabs_create_mcp` → `new_page`
  - `navigate(url, tabId)` 탭 활성화 hack → `select_page(pageId, bringToFront=true)` CDP 네이티브
  - `javascript_tool` → `evaluate_script`
