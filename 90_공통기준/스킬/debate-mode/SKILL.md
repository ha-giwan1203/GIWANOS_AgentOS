---
name: debate-mode
version: v1.3
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v1.3

## 개요

Claude가 브라우저에서 ChatGPT 화면을 직접 읽고, 반박/질문을 생성하여 자동으로 전송하는 반자동 AI 대 AI 토론 스킬.

- API 사용 금지 — 브라우저 자동화만
- **승인 없이 자동 진행** — 반박문 작성 후 즉시 전송, 사용자 승인 대기 없음
- 지정 프로젝트방 전용 운영
- 로컬 로그 파일 저장

---

## 트리거 조건

- "토론모드", "AI 토론", "GPT랑 토론", "debate-mode"
- "GPT 의견 들어봐", "GPT한테 물어봐", "GPT한테 알려줘"
- "ChatGPT에게 반박해", "토론 시작"

---

## 지정 채팅방 (필수)

**새 ChatGPT 대화를 임의로 개설하지 않는다.**

- 프로젝트 URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
- 방 이름: `CLAUDE COWORK 업무 자동화 지침만들기`
- 기존 대화가 없으면 해당 프로젝트 내에서만 새 대화 개설

---

## 핵심 로직

### 1. 텍스트 입력 방식 (v1.3 개선)

```javascript
// 줄바꿈이 포함된 메시지 입력
const textarea = document.querySelector('#prompt-textarea');
const lines = message.split('\n');
textarea.innerHTML = lines.map(l => `<p>${l === '' ? '<br>' : l}</p>`).join('');
textarea.dispatchEvent(new InputEvent('input', { bubbles: true }));

// 전송 — 500ms 후 send-button 클릭
setTimeout(() => {
  document.querySelector('button[data-testid="send-button"]')?.click();
}, 500);
```

> **주의**: `innerHTML` 직접 설정 시 `send-button`이 즉시 감지 안 될 수 있음 → 반드시 `setTimeout 500ms` 후 클릭

### 2. 완료 감지 (2중 조건)

```javascript
// 조건 1: 스트리밍 중지 버튼 소멸
// polling: button[aria-label="스트리밍 중지"] 가 false 될 때까지 대기

// 조건 2: 텍스트 안정성 (소멸 후 5초 대기 후 재확인)
const text1 = getLastAssistantText();
await sleep(3000);
const text2 = getLastAssistantText();
if (text1 === text2) → 완료 확정
```

### 3. 응답 읽기 우선순위

```javascript
// 1순위: .markdown innerText
document.querySelectorAll('[data-message-author-role="assistant"]')
  [last].querySelector('.markdown').innerText

// 2순위: read_page accessibility tree assistant 마지막 블록
// 3순위: get_page_text 전체에서 마지막 "ChatGPT의 말:" 이후
```

---

## 실행 절차

### Step 1. 탭 준비
1. `tabs_context_mcp` — 현재 탭 확인
2. 지정 프로젝트방 이동 또는 기존 대화 URL로 직접 이동
3. 로그 파일 경로 설정: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS`

### Step 2. 초기 메시지 전송
1. 핵심 로직 `1. 텍스트 입력 방식` 사용
2. 스트리밍 완료 감지 (핵심 로직 `2.`)
3. GPT 응답 읽기 (핵심 로직 `3.`)

### Step 3. 반박 생성 및 자동 전송
1. GPT 응답 핵심 주장 3줄 요약
2. 반박 포인트 2~3개 도출 (근거 + 대안 구조)
3. **승인 없이** 바로 Step 2 방식으로 전송
4. 완료 감지 → 읽기 → 반복

### Step 4. 종료 및 마무리
- 설정 턴 수 도달 / "합의" 감지 / 동일 주장 2회 반복 시 종료
- 합의안 + 미합의 쟁점 + 즉시 실행안 3개 도출
- 로그 저장 (`.md` + `.json`)

---

## 오류 대응

| 상황 | 대응 |
|------|------|
| send-button 미감지 | 500ms 추가 대기 후 재시도. 최대 3회 |
| 스트리밍 완료 미감지 | 10초씩 3회 polling. 실패 시 텍스트 안정성만으로 판단 |
| 응답 텍스트 미추출 | fallback 순서대로 (read_page → get_page_text) |
| 로그인 만료 | 사용자에게 재로그인 요청 후 대기 |

---

## 로그 구조

```
90_공통기준/토론모드/logs/
├── debate_YYYYMMDD_HHMMSS.md
└── debate_YYYYMMDD_HHMMSS.json
```

JSON 필수 필드: `session_id`, `chat_url`, `turn_number`, `last_reply_hash`, `turns[]`

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-28 | 초안 |
| v1.1 | 2026-03-29 | 완료 감지 2중 조건, fallback 우선순위 |
| v1.2 | 2026-03-29 | hash 전체 비교, 원문 로그 저장 |
| v1.3 | 2026-03-30 | 전송 로직 개선 (`<p>` 태그 + setTimeout 500ms + data-testid="send-button"), 승인 절차 제거, 지정 채팅방 명확화 |
