---
name: debate-mode
version: v2.5
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v2.5

## 개요

Claude가 브라우저에서 ChatGPT 화면을 직접 읽고, 반박/질문을 생성하여 자동으로 전송하는 반자동 AI 대 AI 토론 스킬.

- API 사용 금지 — 브라우저 자동화만
- **승인 없이 자동 진행** — 반박문 작성 후 즉시 전송, 사용자 승인 대기 없음
- 지정 프로젝트방 전용 운영
- 로컬 로그 파일 저장

## 출력 형식 규칙

Claude와 GPT 모두 표형식 출력 금지.
Markdown table, | 파이프 기반 표, 행/열 비교표, 박스형 표 사용 금지.
모든 응답은 문단형 또는 번호 목록형으로만 작성한다.

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

### 1. 텍스트 입력 방식 (v1.7 개선)

```javascript
const el = document.querySelector('#prompt-textarea');

if (el.tagName === 'TEXTAREA') {
  // --- textarea 경로: native value setter로 React 상태 정상 동기화 ---
  el.focus();
  const proto = Object.getPrototypeOf(el);
  const valueSetter =
    Object.getOwnPropertyDescriptor(proto, 'value')?.set ||
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')?.set;
  valueSetter.call(el, text);
  el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
  el.dispatchEvent(new Event('change', { bubbles: true })); // React fallback
} else {
  // --- contenteditable div 경로: execCommand가 현재 ChatGPT UI에서 가장 안정적 ---
  el.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, text); // deprecated이나 현재 ChatGPT UI에서 안정적 동작
}

// 값 반영 확인 (1순위) → 전송 버튼 활성화 확인 (2순위) → polling 전송
let tries = 0;
const poll = setInterval(() => {
  const valueOk = el.tagName === 'TEXTAREA'
    ? el.value === text
    : el.innerText.trim().length > 0;
  const btn = document.querySelector('button[data-testid="send-button"]');
  const btnReady = btn && btn.disabled === false && btn.getAttribute('aria-disabled') !== 'true';
  if (valueOk && btnReady) {
    btn.click();
    clearInterval(poll);
  } else if (++tries >= 10) {
    clearInterval(poll);
    console.warn('send-button not activated after 3s');
  }
}, 300);
```

> **v1.7 변경**: `innerHTML` 방식 폐기 → native value setter + InputEvent로 교체 (React 상태 정상 동기화). contenteditable div 분기 추가. 전송 버튼 활성화 확인에 값 반영 1순위 + `aria-disabled` 2순위 조건 추가.

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
  → git commit
  → git push origin main  ← 반드시 push 완료 확인 후 다음 단계
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
| PASS (즉시 적용 포함) | 사용자 확인 없이 바로 구현 → commit → **push 완료 확인** → GPT에 최종 완료 보고 |
| 조건부 PASS | GPT가 제시한 수정 항목만 반영 → commit → **push 완료 확인** → GPT 재판정 요청 |
| PASS + 보류 항목 혼재 | PASS 항목만 적용 → 보류 항목은 TASKS.md에 기록 → commit → **push 완료 확인** → GPT 최종 보고 |
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

### Step 1.5. 입력 전 미확인 응답 점검 (필수)

메시지 전송 전 반드시 실행:
1. `[data-message-author-role="assistant"]` 마지막 블록 텍스트 확인
2. `last_reply_hash`와 비교 → 새 응답이 있으면 먼저 읽고 반영
3. 새 응답이 없으면 예정대로 전송 진행

### Step 2. 초기 메시지 전송
1. 핵심 로직 `1. 텍스트 입력 방식` 사용
2. 스트리밍 완료 감지 (핵심 로직 `2.`)
3. GPT 응답 읽기 (핵심 로직 `3.`)

### Step 3. 반박 생성 및 자동 전송
1. GPT 응답 핵심 주장 3줄 요약
2. 반박 포인트 2~3개 도출 (근거 + 대안 구조)
3. **Step 1.5 점검 실행** (미확인 응답 없는지 재확인)
4. **승인 없이** 바로 Step 2 방식으로 전송
5. 완료 감지 → 읽기 → 반복

### Step 4a. 종료 판정
- 설정 턴 수 도달 / "합의" 감지 / 동일 주장 2회 반복 시 종료
- 합의안 + 미합의 쟁점 + 즉시 실행안 3개 도출
- 임시 로그 저장 (`.md` + `.json`) — 아직 최종 확정 아님

### Step 4b. 품질 심층 검토 (critic-reviewer 1회)
1. `critic-reviewer` subagent 호출 — 입력: 토론 로그 .md 파일 경로
2. 4축 평가: 독립성/하네스 엄밀성(필수) + 0건감사/결론 일방성(보조)
3. 판정 처리:
   - **PASS**: 로그에 `[CRITIC] PASS` 기록 → Step 5 진행
   - **WARN**: 로그에 `[CRITIC] WARN — {사유}` 기록 + 사용자 경고 → Step 5 진행
   - **FAIL**: 로그에 `[CRITIC] FAIL — {사유}` 기록 + 사용자 품질 경고 → Step 5 진행 전 경고 표시
4. 세션당 1회만 호출 (재호출 금지)
5. critic 판정 결과를 .json 로그의 `critic_review` 필드에 저장

### Step 5. 산출물 저장 → GitHub 푸시 → GPT 최종 검증 (필수)

> **토론/공동작업으로 생성된 산출물이 있으면 반드시 이 단계까지 완료해야 루틴이 끝난다.**
> Step 4에서 멈추지 않는다.

#### 5-0. GPT 제안·지적 내용 검증 (필수 — 파일 반영/수정 전)

> GPT가 생성한 문서·규칙·코드를 반영하거나, GPT 지적(조건부 PASS/FAIL/수정 필요)에 따라 파일을 수정하기 전에 반드시 이 단계를 수행한다.
> 검증 없이 GPT 출력을 그대로 붙여넣거나, GPT 지적을 실물 확인 없이 수용하는 것은 금지다.

1. 대상 파일 전체 읽기 (Read 도구 사용)
2. GPT 제안 항목별 판정:
   - **신규**: 기존에 없는 내용 → 반영 가능
   - **중복**: 이미 동일하거나 유사한 내용 존재 → 제거
   - **충돌**: 기존 규칙과 상반되는 내용 → 제거 또는 기존 규칙 우선
3. 신규 항목만 선별하여 반영. 충돌·중복 항목은 반영하지 않는다
4. 검증 결과(신규/중복/충돌 분류)를 사용자에게 보고하고, 신규 항목만 반영한다. 승인 대기는 두지 않는다

#### 5-1. 산출물 저장
- 토론 결과로 생성된 파일(SKILL.md, RUNBOOK.md, eval_cases.md 등)을 프로젝트 적정 경로에 저장
- `.skill` 패키지가 필요한 경우 ZIP 재패키징

#### 5-2. GitHub 커밋 + 푸시
```
git add <변경 파일>
git commit -m "feat/fix: [내용] — GPT+Claude 공동작업 결과물"
git push origin main
```
- push 완료 확인 후 다음 단계 진행 (push 전 GPT 보고 금지)

#### 5-3. GPT 최종 검증 요청
GPT 지정 채팅방에 아래 형식으로 전송:
```
파일 저장 및 GitHub 푸시 완료했습니다. 최종 검증 부탁드립니다.

저장된 파일: [파일 목록]
커밋: [commit message]
GitHub: [repo URL]

검증 요청: [구체적 검증 항목 1~4개]
```

#### 5-4. GPT 판정에 따른 분기

> **GPT Evaluator 루틴의 자동 분기 규칙을 그대로 따른다.** 별도 판정 기준을 두지 않는다.

| GPT 판정 | Claude 행동 |
|----------|------------|
| PASS (즉시 적용 포함) | 루틴 종료 → 사용자에게 완료 보고 |
| 조건부 PASS | **Step 5-0 재수행**(지적 파일 Read → 사실 여부 확인 → 맞으면 수정, 틀리면 반론) → 재커밋 → 재푸시 → Step 5-3 반복 |
| PASS + 보류 혼재 | PASS 항목은 **Step 5-0 재수행** 후 반영 → 보류 항목은 TASKS.md 기록 → 재커밋 → 재푸시 → GPT 최종 보고 |
| HOLD (단독) | 작업 중단 → 사용자에게 보류 사유 보고 후 대기 |
| FAIL / 재검토 | **Step 5-0 재수행**(지적 파일 Read → 사실 여부 확인) → 수정 후 재보고 (최대 2회) → 동일 FAIL 2회 시 사용자에게 보고 후 중단 |

#### 5-5. PASS 완료 보고 형식 (사용자에게)
```
완료 보고
- 산출물: [파일/패키지 목록]
- GitHub: [repo URL] / [commit SHA]
- GPT 판정: PASS
- 잔여 이슈: 없음 / [있으면 1줄]
```

#### 5-6. Step 5 전용 오류 경로

| 상황 | 대응 |
|------|------|
| git push 실패 | 오류 메시지 확인 → 인증/충돌 원인 파악 → 사용자에게 보고 후 대기 |
| GPT 채팅방 전송 실패 | 탭 재로드 → 재전송 시도 1회 → 실패 시 사용자에게 보고 |
| GPT 검증 응답 시간 초과 (5회×10초) | 사용자에게 "GPT 응답 없음" 보고 후 중단 |

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

JSON 필수 필드: `session_id`, `chat_url`, `turn_number`, `last_reply_hash`, `turns[]`, `critic_review`

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
| v1.7 | 2026-03-30 | 입력 방식 교체: innerHTML 폐기 → native value setter + InputEvent (React 상태 정상 동기화). contenteditable div 분기 추가. 전송 버튼 확인 로직 개선 (값 반영 1차, aria-disabled 포함 버튼 활성화 2차) |
| v1.8 | 2026-03-30 | 출력 형식 규칙 추가: Claude/GPT 모두 표형식 출력 금지. 문단형/번호 목록형만 허용 |
| v1.9 | 2026-03-30 | Step 1.5 신설: 입력 전 미확인 GPT 응답 점검 필수화. Step 3에 재확인 단계 추가 |
| v2.0 | 2026-03-30 | GPT 보고 순서 강제: commit → push 완료 확인 → GPT 전송. push 전 GPT 보고 금지 |
| v2.1 | 2026-03-30 | Step 5 신설: 산출물 저장 → GitHub 푸시 → GPT 최종 검증 → PASS 판정까지 루틴 필수화. Step 4에서 루틴이 끊기는 문제 해결 |
| v2.2 | 2026-03-30 | Step 5 보완: 5-4 판정 분기를 GPT Evaluator 참조형으로 교체(중복 제거), HOLD/PASS+보류 혼재 추가, 5-5 완료 보고 형식 추가, 5-6 Step 5 전용 오류 경로 추가 |
| v2.3 | 2026-03-30 | Step 5-0 신설: GPT 제안 내용 검증 필수화 (파일 반영 전 신규/중복/충돌 판정 → 신규만 반영) |
| v2.4 | 2026-04-02 | ENTRY.md PRIMARY 분리, REFERENCE.md 신설, 하네스 분석 규칙 강화 |
| v2.5 | 2026-04-07 | Step 4 → 4a/4b 분리: critic-reviewer subagent 세션 종료 1회 호출. 2필수(독립성/하네스)+2보조(0건감사/일방성) 4축 평가 |
