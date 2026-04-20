# GPT 응답 읽기

GPT 프로젝트방의 최신 응답을 읽어오는 단일 명령.
토론모드·share-result에서 응답 확인 시 공통 호출한다.

## 실행 순서

### 1. 탭 확인
- `tabs_context_mcp` → 기존 ChatGPT 탭 확인
- ChatGPT 탭이 없으면: `.claude/state/debate_chat_url` 읽기 → navigate

### 2. 응답 완료 + 안정성 확인 (세션69 개선, 세션83 thinking 확장)

2-a. **thinking 모델 감지 + stop-button 병행 판정** (세션83 Round 1, 3자 API 합의):
```javascript
(() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  const last = blocks.length ? blocks[blocks.length - 1] : null;
  const slug = (last && last.getAttribute('data-message-model-slug') || '').toLowerCase();
  const isExtended = slug.includes('thinking') || slug.includes('reasoning');
  const stopBtn = document.querySelector('[data-testid="stop-button"]') !== null;
  const lastText = last ? (last.innerText || '').trim() : '';
  return JSON.stringify({
    isExtended, slug, stopBtn,
    maxTimeout: isExtended ? 600 : 300,
    lastLen: lastText.length,
    lastSlice: lastText.slice(-100)
  });
})();
```

**폴링 정책**:
- `isExtended=false`: 3/5/8초 단계, 최대 300초 (기존 유지)
- `isExtended=true`: 3/5/8/15초 반복, 300초 이후만 30초 단계로 전환, 최대 600초
- **종료 판정은 stop-button 단독으로 하지 않음** (세션82 실증: thinking 중 stop-button 지속 유지되며 Claude가 오클릭)
  - 종료 조건 OR:
    1. `stopBtn=false` AND 2-b 안정성(2회 연속 동일) PASS (기존 경로)
    2. 블록 안정 3회 연속 동일 (`lastLen`·`lastSlice` 3회 동일) → stop-button 잔존 무관 완료 판정 (세션83 신설, thinking 응답 완결 후 DOM 안정 보장)

**slug 정규화 이유 (GPT-5.2·Gemini 3.1-pro-preview 교차 검증)**:
- `toLowerCase().includes('thinking' or 'reasoning')`: 향후 `-thinking-v2`, `-reasoning-exp`, `-thinking-preview` 변형 대응
- `endsWith('-thinking')`만으로는 미래 slug 변형 누락 위험 (Gemini 지적)
- 과도한 allowlist는 유지보수 부담 (GPT-5.2 우려 부분 반영하되 단순화)

2-b. **마지막 유효 블록 안정성 확인** (placeholder 스킵 + 2회 연속 동일 여부):
```javascript
(() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  // 뒤에서 역순 스캔해서 len>=30 인 첫 블록 반환 (placeholder 스킵)
  for (let i = blocks.length - 1; i >= 0; i--) {
    const t = (blocks[i].innerText || '').trim();
    if (t.length >= 30) return JSON.stringify({idx: i, len: t.length, lastSlice: t.slice(-100)});
  }
  return JSON.stringify({idx: -1, len: 0, lastSlice: ''});
})();
```
- 2초 간격으로 2회 측정, `len`·`lastSlice` 동일하면 안정 판정 → 3으로
- 변화 중이면 stop-button 다시 확인

### 3. 최신 응답 읽기 (placeholder 스킵 + 한 번에 전체 반환 — 세션79 속도 개선)

```javascript
(() => {
  const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
  for (let i = blocks.length - 1; i >= 0; i--) {
    const t = (blocks[i].innerText || '').trim();
    if (t.length >= 30) {
      // 세션79 속도 개선: 첫 호출에서 길이 + 전체 텍스트 반환 → 분할 slice 호출 제거
      return JSON.stringify({
        len: t.length,
        text: t  // MCP가 자동 truncate해도 len으로 전체 크기 파악 가능, 필요시만 slice 후속 호출
      });
    }
  }
  return JSON.stringify({len: 0, text: ''});
})();
```

**반환 해석**: MCP tool result는 최대 ~1200자에서 truncate되는 경향 있음. `len`이 이보다 크면 `txt.slice(1200)` 1회만 추가 호출. 장문 응답도 최대 2회 호출로 완결(기존 3~4회 → 2회).

### 3-prep. 백그라운드 throttling 대응 (세션70 실증 — 필수)

**먼저** 대상 탭을 foreground로 강제 전환한다. visibility 이벤트 dispatchEvent만으로는 실제 Chrome throttling을 풀지 못한다(세션69 실패 사례). 진짜 회피는 `navigate` 재호출이다.

```
navigate(url=debate_chat_url, tabId=gpt_tab_id)  # 동일 URL 재호출 → 탭 foreground 전환
```

- Chrome MCP는 activate API 미제공. navigate 재호출이 유일 회피 경로.
- navigate는 동일 URL이라도 탭 포커스를 전환하며 페이지 상태는 보존.
- 보조: 그래도 hidden 감지되면 visibility 이벤트 트리거:
```javascript
if (document.visibilityState === 'hidden') {
  document.dispatchEvent(new Event('visibilitychange'));
}
```
- 상세: `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" 참조

### 3-retry. 읽기 실패 시 재시도

반환 텍스트가 비었거나 `len<30`이면:
1. `sleep 3` 후 3단계 재시도 (최대 3회)
2. 여전히 실패면 `navigate` 재호출(동일 URL)로 탭 포커스 전환 → 5초 대기 → 재시도
3. 그래도 실패면 `navigate` reload(실제 페이지 새로고침) → 10초 대기 → 재시도
4. 최종 실패 시 "GPT 응답 감지 실패 — 탭 수동 활성화 필요" 보고

### 4. 판정 키워드 추출 (optional)
응답에서 판정 키워드를 자동 감지한다. **우선순위 높은 것부터 먼저 매칭** — 첫 매칭 승리:

1. **실패** (최우선): "실패", "재검토", "수정 필요", "권장하지 않습니다"
2. **부분반영**: "부분반영", "부분 반영"
3. **조건부**: "조건부 통과", "이 항목만 보정하면 진행", "소규모 보정 후 진행"
4. **정합**: "정합", "코드 정합", "코드 품질"
5. **통과** (최하위): "즉시 적용", "바로 적용", "적용 권장", "통과", "문제 없습니다", "진행하면 됩니다"

- "조건부 통과"는 "통과"보다 먼저 매칭되므로 오분류 방지
- 감지된 판정과 원문 키워드를 함께 보고한다.

### 5. 비통과 판정 시 incident 기록 (세션45 B1)
판정이 "통과" 이외일 때 학습 루프에 기록한다:

```bash
python3 .claude/hooks/record_incident.py \
  --type gpt_verdict \
  --hook gpt-read \
  --detail "GPT 판정: {판정결과} — {원문 키워드}" \
  --field source=gpt \
  --field verdict={판정코드} \
  --field classification_reason=gpt_verdict \
  --quiet
```

판정코드 매핑:
- 실패 → `fail`
- 부분반영 → `partial`
- 조건부 → `conditional`
- 정합 → `consistency`
- 통과 → 기록 안 함 (정상)

## 에러 처리
- 탭 소실: `tabs_context_mcp`(createIfEmpty=true) 후 재진입
- assistant 블록 없음 or 전부 len<30: 3-retry 절차 수행
- 300초 타임아웃: "GPT 응답 타임아웃" 보고 후 중단

## 변경 이력
- 세션69 (2026-04-18): 근본 버그 수정
  - 마지막 블록 len=0 placeholder 스킵 (역순 len>=30 스캔)
  - 2회 연속 동일 측정 안정성 판정
  - 백그라운드 throttling 대응 (visibilitychange 트리거)
  - 읽기 실패 시 자동 재시도 (sleep → navigate reload → 수동 요청)
- 세션83 (2026-04-20): thinking 모델 확장 추론 대응 (3자 API 예외 합의)
  - `data-message-model-slug` includes `thinking`/`reasoning` lowercase 매칭
  - isExtended=true 시 maxTimeout 300→600초 + 후기 30초 단계 도입
  - stop-button 단독 판정 금지 — 블록 안정 3회 연속 동일 종료 경로 추가 (stop-button 잔존 대비)
  - 세션82 실증: gpt-5-4-thinking 응답 중 stop 오클릭 사건 해소
