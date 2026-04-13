# GPT 응답 읽기

GPT 프로젝트방의 최신 응답을 읽어오는 단일 명령.
토론모드·share-result에서 응답 확인 시 공통 호출한다.

## 실행 순서

### 1. 탭 확인
- `tabs_context_mcp` → 기존 ChatGPT 탭 확인
- ChatGPT 탭이 없으면: `.claude/state/debate_chat_url` 읽기 → navigate

### 2. 응답 완료 확인
```javascript
document.querySelector('[data-testid="stop-button"]') !== null
```
- true면 아직 생성 중 → 적응형 polling 대기 (3/5/8초, 최대 300초)
- false면 완료

### 3. 최신 응답 읽기
```javascript
const blocks = document.querySelectorAll('[data-message-author-role="assistant"]');
const last = blocks[blocks.length - 1];
last ? last.innerText : '';
```
- 응답 텍스트를 반환

### 4. 판정 키워드 추출 (optional)
응답에서 판정 키워드를 자동 감지:
- 통과: "즉시 적용", "바로 적용", "적용 권장", "통과", "문제 없습니다", "진행하면 됩니다"
- 조건부: "조건부 통과", "이 항목만 보정하면 진행", "소규모 보정 후 진행"
- 실패: "보류", "실패", "재검토", "수정 필요", "문제 있습니다"
- 정합: "정합", "코드 정합", "코드 품질"
- 부분반영: "부분반영", "부분 반영"

감지된 키워드를 함께 보고한다.

## 에러 처리
- 탭 소실: `tabs_context_mcp`(createIfEmpty=true) 후 재진입
- assistant 블록 없음: "GPT 응답 없음" 보고
- 300초 타임아웃: "GPT 응답 타임아웃" 보고 후 중단
