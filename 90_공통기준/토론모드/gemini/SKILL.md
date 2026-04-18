# /gemini-debate — Gemini API 토론 스킬

## 용도
Gemini 2.5-flash API를 상대로 특정 주제를 멀티턴 토론.
GPT 토론(브라우저 자동화)과 달리 API 직접 호출 → 안정적.

## 실행 방식

### 인터랙티브 모드 (Claude가 반박 직접 입력)
```bash
source ~/.gemini/api_key.env
python 90_공통기준/토론모드/gemini/gemini_debate.py \
  --topic "주제" \
  --rounds 3
```

### API 단발 호출 (Claude가 자동 반박 생성)
```bash
source ~/.gemini/api_key.env
curl -sS https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"<주제+입장>"}]}]}'
```

## 토론 루프
1. Claude 오프닝 입장 작성
2. Gemini API 전송 → 응답 수신
3. 하네스 분석 (채택/보류/버림)
4. Claude 반박 생성 → Gemini 전송
5. 반복 (기본 3 라운드)

## 하네스 분석 규칙 (GPT 토론모드와 동일)
- 주장 2~4개 분해
- 라벨: 실증됨 / 일반론 / 환경미스매치 / 과잉설계
- 판정: 채택 / 보류 / 버림
- 반박 첫 문단에 `채택: N건 / 보류: N건 / 버림: N건` 필수

## 로그
- 저장 위치: `gemini/logs/debate_YYYYMMDD_HHMMSS.jsonl`
- 형식: topic + rounds 배열 (role/text/round)

## 차이점 (GPT 토론 vs Gemini 토론)
| 항목 | GPT 토론 | Gemini 토론 |
|------|---------|------------|
| 전달 방식 | Chrome MCP 브라우저 | API 직접 호출 |
| 안정성 | 셀렉터 의존, 불안정 | API → 안정적 |
| 비용 | ChatGPT Pro 구독 | 토큰당 과금 (₩10K 캡) |
| 멀티모달 | 텍스트 위주 | 영상·이미지 포함 가능 |
