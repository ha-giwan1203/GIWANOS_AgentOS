# /gemini-send — Gemini 웹 UI 조작 스킬

## 사용 원칙
**웹 UI 우선**: 기본은 `gemini.google.com` Chrome MCP 조작.
API 호출은 Grounding(실시간 검색), 배치 처리 등 웹 UI로 불가한 경우에만 예외 사용.

## Gem 정보
- Gem URL: `https://gemini.google.com/gem/3333ff7eb4ba`
- 채팅방 URL: `.claude/state/gemini_chat_url` 참조 (세션마다 현재 탭 URL로 갱신)

## 웹 UI 스킬 (주)

### 메시지 전송
```
Skill(skill="gemini-send", args="메시지 텍스트")
```

### 응답 읽기
```
Skill(skill="gemini-read")
```

## 웹 UI 고정 셀렉터
```
입력창:    .ql-editor                        (contenteditable DIV)
전송버튼:  [aria-label="메시지 보내기"]       (BUTTON)
응답 노드: model-response                    (커스텀 엘리먼트)
완료 감지: [aria-label="메시지 보내기"] aria-disabled="false"
입력 방식: document.execCommand('insertText', false, text)  ← 확인 완료
```

## API 호출 (예외 — 웹 UI 불가 시에만)

### 단발 호출
```bash
source ~/.gemini/api_key.env
curl -sS "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"주제+입장"}]}]}'
```

### Grounding (실시간 웹 검색) — API 전용 기능
```bash
source ~/.gemini/api_key.env
curl -sS "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents":[{"role":"user","parts":[{"text":"질문"}]}],
    "tools":[{"googleSearch":{}}]
  }'
```

### 멀티턴 스크립트
```bash
source ~/.gemini/api_key.env
python 90_공통기준/토론모드/gemini/gemini_debate.py \
  --topic "주제" \
  --rounds 3
```

## 하네스 분석 규칙 (Gemini 응답에 동일 적용)
- 주장 2~4개 분해
- 라벨: 실증됨 / 일반론 / 환경미스매치 / 과잉설계
- 판정: 채택 / 보류 / 버림
- 반박 첫 문단에 `채택: N건 / 보류: N건 / 버림: N건` 필수

## 로그
- API 멀티턴 로그: `gemini/logs/debate_YYYYMMDD_HHMMSS.jsonl`
- 웹 UI 토론 로그: `90_공통기준/토론모드/logs/` (debate-mode와 동일 위치)

## 방식 비교

| 항목 | 웹 UI (주) | API (예외) |
|------|-----------|-----------|
| 사용 방법 | Chrome MCP 브라우저 | curl / Python |
| Gem 시스템 프롬프트 | 자동 적용 | 수동 삽입 필요 |
| 대화 히스토리 | 웹에 자동 저장 | 코드에서 관리 |
| Grounding | 웹 UI 설정 ON 시 | `"googleSearch":{}` 도구 |
| 비용 | 구독 포함 | 토큰당 과금 (₩10K 캡) |
| 멀티모달 | 드래그앤드롭 | fileData API |

## GPT 토론 vs Gemini 토론

| 항목 | GPT 토론 | Gemini 토론 |
|------|---------|------------|
| 전달 방식 | Chrome MCP (gpt-send) | Chrome MCP (gemini-send) |
| 안정성 | 셀렉터 의존 | 셀렉터 의존 |
| 비용 | ChatGPT Pro 구독 | 구독 포함 |
| 멀티모달 | 텍스트 위주 | 영상·이미지 네이티브 |
| Grounding | 없음 | 웹 검색 내장 |
