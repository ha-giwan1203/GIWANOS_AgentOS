# Gemini 응답 읽기

Gemini 웹 UI의 최신 응답을 읽어오는 단일 명령.
토론모드·gemini-send에서 응답 확인 시 공통 호출한다.

## 실행 순서

### 1. 탭 확인
- `tabs_context_mcp` → `gemini.google.com` 포함 탭 확인
- 없으면: `.claude/state/gemini_chat_url` 읽기 → navigate

### 2. 응답 완료 대기

```javascript
// 전송 버튼 aria-disabled=false → 완료, true → 생성 중
const btn = document.querySelector('[aria-label="메시지 보내기"]');
btn ? btn.getAttribute('aria-disabled') : 'not_found';
```

- `"true"` 또는 `'not_found'` → 적응형 polling (3/5/8초, 최대 300초)
- `"false"` → 완료

### 3. 최신 응답 읽기

```javascript
const blocks = document.querySelectorAll('model-response');
const last = blocks[blocks.length - 1];
last ? last.innerText : '';
```

- 응답 텍스트를 반환

### 4. 판정 키워드 추출 (optional)

응답에서 판정 키워드를 자동 감지한다. 우선순위 높은 것부터 매칭:

1. **실패** (최우선): "실패", "재검토", "수정 필요", "권장하지 않습니다"
2. **부분반영**: "부분반영", "부분 반영"
3. **조건부**: "조건부 통과", "이 항목만 보정하면", "소규모 보정 후"
4. **정합**: "정합", "코드 정합"
5. **통과** (최하위): "즉시 적용", "바로 적용", "통과", "문제 없습니다"

## 에러 처리
- 탭 소실: `tabs_context_mcp(createIfEmpty=true)` → gemini_chat_url로 재진입
- model-response 없음: "Gemini 응답 없음" 보고
- 300초 타임아웃: "Gemini 응답 타임아웃" 보고 후 중단

## 고정 셀렉터 참조
```
응답 노드: model-response
완료 감지: [aria-label="메시지 보내기"] aria-disabled="false"
```
