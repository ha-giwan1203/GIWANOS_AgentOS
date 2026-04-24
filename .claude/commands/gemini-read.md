# Gemini 응답 읽기 (chrome-devtools-mcp 기반)

Gemini 웹 UI의 최신 응답을 읽어오는 단일 명령.
토론모드·gemini-send에서 응답 확인 시 공통 호출한다.

**2026-04-24 세션105 마이그레이션**: claude-in-chrome → chrome-devtools-mcp.
CDP Chrome(포트 9222) 기동 필수.

## 실행 순서

### 1. 페이지 확인
- `mcp__chrome-devtools-mcp__list_pages` → `gemini.google.com` 포함 페이지 확인
- 없으면: `.claude/state/gemini_chat_url` 읽기 → `new_page(url=<gemini_chat_url>)` 또는 `select_page` + `navigate_page`

### 2. 응답 완료 + 안정성 확인 (세션69 개선)

2-a. **전송 버튼 상태 감지** (fallback 셀렉터 3중):

`mcp__chrome-devtools-mcp__evaluate_script`:
```javascript
() => {
  const sel1 = document.querySelector('[aria-label="메시지 보내기"]');
  const sel2 = document.querySelector('button[aria-label*="보내기"]');
  const sel3 = document.querySelector('button.send-button, button[jsname][mat-icon-button]');
  const btn = sel1 || sel2 || sel3;
  return btn ? btn.getAttribute('aria-disabled') : 'not_found';
}
```
- `"true"` → 생성 중 → 적응형 polling (3/5/8초, 최대 300초)
- `"not_found"` → DOM 재구성 중 → 2초 대기 후 재시도 (최대 5회). 5회 초과 시 `navigate_page(type="reload")`
- `"false"` → 2-b로

2-b. **마지막 유효 블록 안정성 확인** (placeholder 스킵 + 2회 연속 동일 여부):
```javascript
() => {
  const blocks = document.querySelectorAll('model-response');
  for (let i = blocks.length - 1; i >= 0; i--) {
    const t = (blocks[i].innerText || '').trim();
    // Gemini 기본 메타 텍스트("C\nClaude-Gemini...") 제외
    const cleaned = t.replace(/^C\s*Claude-Gemini[^\n]*\n사용자설정 Gem[^\n]*\n[^\n]*\n[^\n]*\n/, '').trim();
    if (cleaned.length >= 30) return {idx: i, len: cleaned.length, lastSlice: cleaned.slice(-100)};
  }
  return {idx: -1, len: 0, lastSlice: ''};
}
```
- 2초 간격으로 2회 측정, `len`·`lastSlice` 동일하면 안정 판정 → 3으로

### 3. 최신 응답 읽기 (placeholder·메타 스킵 + 한 번에 전체 반환 — 세션79 속도 개선)

```javascript
() => {
  const blocks = document.querySelectorAll('model-response');
  for (let i = blocks.length - 1; i >= 0; i--) {
    const t = (blocks[i].innerText || '').trim();
    const cleaned = t.replace(/^C\s*Claude-Gemini[^\n]*\n사용자설정 Gem[^\n]*\n[^\n]*\n[^\n]*\n/, '').trim();
    if (cleaned.length >= 30) {
      return { len: cleaned.length, text: cleaned };
    }
  }
  return { len: 0, text: '' };
}
```

**반환 해석**: MCP tool result 자동 truncate 시 `len`으로 전체 크기 파악. 필요시 `text.slice(1200)` 1회 추가 호출로 완결.

### 3-prep. 백그라운드 throttling 대응 (세션105 마이그레이션 — CDP 네이티브)

**먼저** 대상 페이지를 foreground로 강제 전환한다. `select_page(bringToFront=true)`가 CDP `Target.activateTarget`을 직접 호출해 throttling 해소.

```
mcp__chrome-devtools-mcp__select_page(pageId=<gemini_page_id>, bringToFront=true)
```

- URL 재진입 불필요 — 탭 포커스 전환만
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 3-retry. 읽기 실패 시 재시도

반환 텍스트가 비었거나 `len<30`이면:
1. `sleep 3` 후 3단계 재시도 (최대 3회)
2. 여전히 실패면 `select_page(bringToFront=true)` 재호출 → 5초 대기 → 재시도
3. 그래도 실패면 `navigate_page(type="reload")` → 10초 대기 → 재시도
4. 최종 실패 시 "Gemini 응답 감지 실패 — 탭 수동 활성화 필요" 보고

### 4. 판정 키워드 추출 (optional)

응답에서 판정 키워드를 자동 감지한다. 우선순위 높은 것부터 매칭:

1. **실패** (최우선): "실패", "재검토", "수정 필요", "권장하지 않습니다"
2. **부분반영**: "부분반영", "부분 반영"
3. **조건부**: "조건부 통과", "이 항목만 보정하면", "소규모 보정 후"
4. **정합**: "정합", "코드 정합"
5. **통과** (최하위): "즉시 적용", "바로 적용", "통과", "문제 없습니다"

## 에러 처리
- 페이지 소실: `list_pages` → 없으면 `new_page(url=<gemini_chat_url>)` 재진입
- model-response 없음 or 전부 cleaned<30: 3-retry 절차 수행
- 300초 타임아웃: "Gemini 응답 타임아웃" 보고 후 중단

## 고정 셀렉터 참조
```
응답 노드: model-response
전송버튼 primary:  [aria-label="메시지 보내기"]
전송버튼 fallback: button[aria-label*="보내기"], button.send-button, button[jsname][mat-icon-button]
완료 감지: aria-disabled="false"
메타 텍스트 정규식: /^C\s*Claude-Gemini[^\n]*\n사용자설정 Gem[^\n]*\n[^\n]*\n[^\n]*\n/
```

## 변경 이력
- 세션69 (2026-04-18): 근본 버그 수정
  - placeholder + 메타 텍스트 스킵 (역순 cleaned>=30 스캔)
  - 전송 버튼 셀렉터 fallback 3중
  - `not_found` 5회 재시도 → navigate reload 자동 전환
  - 2회 연속 동일 측정 안정성 판정
  - 백그라운드 throttling 대응
  - 읽기 실패 시 자동 재시도
- 세션105 (2026-04-24): claude-in-chrome → chrome-devtools-mcp 전면 마이그레이션
  - `tabs_context_mcp` → `list_pages`
  - `navigate(url, tabId)` 탭 활성화 hack → `select_page(pageId, bringToFront=true)` CDP 네이티브
  - `javascript_tool` → `evaluate_script`
