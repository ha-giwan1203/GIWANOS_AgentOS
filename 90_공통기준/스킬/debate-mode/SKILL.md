---
name: debate-mode
version: v1.6
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v1.6

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

### 1. 텍스트 입력 방식 (v1.4 개선)

```javascript
// HTML 특수문자 escape
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// 줄바꿈이 포함된 메시지 입력
const textarea = document.querySelector('#prompt-textarea');
const lines = message.split('\n');
textarea.innerHTML = lines.map(l => `<p>${l === '' ? '<br>' : escapeHtml(l)}</p>`).join('');
textarea.dispatchEvent(new InputEvent('input', { bubbles: true }));

// 전송 — send-button polling (최대 10회 × 300ms)
let tries = 0;
const poll = setInterval(() => {
  const btn = document.querySelector('button[data-testid="send-button"]');
  if (btn && !btn.disabled) {
    btn.click();
    clearInterval(poll);
  } else if (++tries >= 10) {
    clearInterval(poll);
    console.warn('send-button not found after 3s');
  }
}, 300);
```

> **v1.4 변경**: HTML escape 추가 (< > & 문자 입력 오류 방지), setTimeout → polling으로 전환 (버튼 활성화 타이밍 대응)

### 2. 완료 감지 (get_page_text 텍스트 비교 방식)

> JS 폴링(setInterval)은 CDP 45초 타임아웃으로 사용 불가. send-button/스트리밍 버튼 셀렉터는 GPT UI 버전에 따라 없을 수 있음.
> **유일하게 신뢰 가능한 방법: get_page_text 2회 비교**

```
Step 1. 전송 직후 get_page_text → text_before 저장
Step 2. 10초 대기 (Bash sleep 또는 다음 tool call 자연 지연)
Step 3. get_page_text → text_after
Step 4. text_before == text_after → 아직 미응답 → 10초 더 대기 후 재시도
         text_before != text_after AND 마지막 발화자가 assistant → 완료 판정
Step 5. 최대 5회(50초) 반복. 초과 시 사용자에게 "GPT 응답 대기 중" 보고
```

완료 판정 기준: `[data-message-author-role="assistant"]` 마지막 블록이 내 전송 메시지 이후에 추가됨

### 3. 응답 읽기 우선순위

```javascript
// 1순위: .markdown innerText
document.querySelectorAll('[data-message-author-role="assistant"]')
  [last].querySelector('.markdown').innerText

// 2순위: read_page accessibility tree assistant 마지막 블록
// 3순위: get_page_text 전체에서 마지막 "ChatGPT의 말:" 이후
```

---

## GPT Evaluator 루틴 (report 모드)

> **이 루틴이 작동하지 않으면 "토론모드 고장" 증상이 발생한다.**

트리거: "gpt한테 보고", "gpt한테 알려줘", "gpt 승인 받아", "gpt한테 확인해", "보고 하고 승인 받아"

### 루틴 흐름

```
Claude 작업 완료
  → GPT 지정 채팅방에 완료 보고 전송 (SHA + 변경 내용 + 질문)
  → GPT 응답 대기 (완료 감지 로직 사용)
  → GPT 응답에서 판정 추출
  → 판정에 따라 자동 분기
```

### PASS 판정 키워드 (감지 시 자동 진행)

다음 중 하나라도 있으면 **PASS**로 간주하고 사용자 확인 없이 다음 작업 진행:

- "즉시 적용", "지금 바로 적용", "바로 적용", "적용 권장"
- "PASS", "통과", "합격"
- "문제 없습니다", "진행하면 됩니다", "적용하면 됩니다"

### HOLD / FAIL 판정 키워드 (감지 시 사용자에게 보고 후 대기)

- "보류", "FAIL", "재검토", "수정 필요", "문제 있습니다"
- "하지 마십시오", "권장하지 않습니다"

### 자동 분기 규칙

| GPT 판정 | Claude 행동 |
|----------|------------|
| PASS (즉시 적용 포함) | 사용자 확인 없이 바로 구현 → GitHub push → GPT에 최종 완료 보고 |
| 조건부 PASS | GPT가 제시한 수정 항목만 반영 → push → GPT 재판정 요청 |
| PASS + 보류 항목 혼재 | PASS 항목만 적용 → 보류 항목은 TASKS.md에 기록 → push → GPT 최종 보고 |
| HOLD (단독) | 작업 중단 → 사용자에게 보류 사유 보고 후 대기 |
| FAIL / 재검토 | 수정 내용 파악 → 수정 후 재보고 (최대 2회) → 동일 FAIL 2회 시 사용자에게 보고 후 중단 |

> **핵심 규칙**: GPT가 "즉시 적용"을 포함한 PASS 판정을 내리면 Claude는 사용자에게 "바로 적용할까요?" 같은 확인 질문을 **절대 하지 않는다**. 바로 실행한다.

---

## 실행 절차

### Step 1. 탭 준비
1. `tabs_context_mcp` — 현재 탭 확인
2. **chat_url 재사용 우선**: 최신 로그 JSON에서 `chat_url` 읽기 → 해당 URL로 직접 이동
   - 로그 없으면: 지정 프로젝트방(`https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`) 이동 후 새 대화 개설
3. 로그 파일 경로 설정: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS`
4. 첫 메시지 전송 후 URL이 `/c/` 형태로 바뀌면 즉시 `chat_url`을 로그 JSON에 저장

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
| send-button 미감지 | get_page_text 텍스트 비교 방식으로 대체 (send-button은 GPT UI 버전에 따라 없을 수 있음) |
| 스트리밍 완료 미감지 | get_page_text 10초 간격 최대 5회 비교. 텍스트 변화 없으면 사용자에게 보고 |
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
| v1.4 | 2026-03-30 | HTML escape 추가, setTimeout → send-button polling (300ms×10회), chat_url 재사용 로직 명시 |
| v1.4.1 | 2026-03-30 | 오류 대응 표 polling 문구 통일, 완료 감지 대기 5초→3초 통일 |
| v1.5 | 2026-03-30 | GPT Evaluator 루틴 추가 — PASS/FAIL 키워드 자동 감지 + 판정에 따른 자동 분기. "바로 적용할까요?" 재확인 버그 수정 |
| v1.6 | 2026-03-30 | 완료 감지 로직 전면 교체 — JS 폴링(CDP 타임아웃) 제거, get_page_text 10초 간격 5회 텍스트 비교 방식으로 대체. send-button 셀렉터 의존 제거 |
