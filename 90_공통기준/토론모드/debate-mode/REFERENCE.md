# 토론모드 상세 참조 (REFERENCE.md)

> SKILL.md 코어에서 분리된 기술 상세. 실행 중 필요 시 참조.
> 앱 운영 규칙과 문서 우선순위는 상위 `../CLAUDE.md`, `../APP_INSTRUCTIONS.md`를 따른다.
> 토론방에 보내는 자연어 본문은 한국어만 사용한다. 예외: code block, selector/data-testid, 파일 경로, commit SHA 같은 literal, 그리고 `오류 원문:`/`에러 원문:` 라벨 1줄 인용.

> 로컬 CDP 경로에서는 `.claude/scripts/cdp/cdp_chat_send.py --require-korean --mark-send-gate`를 기본 전송 경로로 사용한다. 직접 DOM 전송은 helper를 쓸 수 없을 때만 예비 경로로 사용한다.

---

## 1. 기본 전송 경로 (v2.9 — CDP 단일화)

```bash
python '.claude/scripts/cdp/cdp_chat_send.py' \
  --auto-debate-url \
  --text-file '<utf8_text_file>' \
  --mark-send-gate
```

- `--auto-debate-url`: debate_chat_url 상태 파일에서 URL을 읽어 --match-url-exact로 자동 설정
- `--require-korean`: 비활성화됨 (2026-04-11). 옵션은 호환성 유지를 위해 남아있으나 실제 차단 없음
- `--mark-send-gate`: assistant 최신 읽기 직후 send_gate 파일 갱신
- submit selector는 `[data-testid="send-button"], #composer-submit-button` 순서로 내부 fallback 처리
- 토론모드 문서상 기본 전송 경로는 위 helper다.

### 예비 경로: 직접 DOM 입력 + 전송 (v1.7)

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
  const btn = document.querySelector('button[data-testid="send-button"], #composer-submit-button');
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

> **v2.8 변경**: `cdp_chat_send.py`에 직전 최신 답변 기대값 확인 옵션 추가. helper가 최신 답변 불일치도 직접 막는 기본 경로가 된다.
> **v2.7 변경**: `cdp_chat_send.py`를 문서상 기본 전송 경로로 승격. 직접 DOM 입력/전송은 helper를 쓸 수 없을 때만 예비 경로로 유지.
> **v1.7 변경**: `innerHTML` 방식 폐기 → native value setter + InputEvent로 교체 (React 상태 정상 동기화). contenteditable div 분기 추가. 전송 버튼 활성화 확인에 값 반영 1순위 + `aria-disabled` 2순위 조건 추가.

---

## 2. 완료 감지 (get_page_text 텍스트 비교 방식)

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

---

## 3. 응답 읽기 우선순위

```javascript
// 1순위: .markdown innerText
document.querySelectorAll('[data-message-author-role="assistant"]')
  [last].querySelector('.markdown').innerText

// 2순위: read_page accessibility tree assistant 마지막 블록
// 3순위: get_page_text 전체에서 마지막 "ChatGPT의 말:" 이후
```

---

## 4. 오류 대응

| 상황 | 대응 |
|------|------|
| send-button 미감지 | get_page_text 텍스트 비교 방식으로 대체 |
| 스트리밍 완료 미감지 | get_page_text 10초 간격 최대 5회 비교. 텍스트 변화 없으면 사용자에게 보고 |
| 응답 텍스트 미추출 | fallback 순서대로 (read_page → get_page_text) |
| 로그인 만료 | 사용자에게 재로그인 요청 후 대기 |
| git push 실패 | 오류 메시지 확인 → 인증/충돌 원인 파악 → 사용자에게 보고 후 대기 |
| GPT 채팅방 전송 실패 | 탭 재로드 → 재전송 시도 1회 → 실패 시 사용자에게 보고 |
| GPT 검증 응답 시간 초과 (5회×10초) | 사용자에게 "GPT 응답 없음" 보고 후 중단 |

---

## 5. 로그 구조

```
90_공통기준/토론모드/logs/
├── debate_YYYYMMDD_HHMMSS.md
└── debate_YYYYMMDD_HHMMSS.json
```

JSON 필수 필드: `session_id`, `chat_url`, `turn_number`, `last_reply_hash`, `turns[]`, `result`, `critic_review`

턴별 harness 스키마 → SKILL.md "로그" 섹션 참조. 핵심: `summary_counts`(숫자) + 채택/보류/버림 각각 `{item, label, evidence, ref}` 배열.

---

## 6. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-28 | 초안 |
| v1.1 | 2026-03-29 | 완료 감지 2중 조건, fallback 우선순위 |
| v1.2 | 2026-03-29 | hash 전체 비교, 원문 로그 저장 |
| v1.3 | 2026-03-30 | 전송 로직 개선, 승인 절차 제거, 지정 채팅방 명확화 |
| v1.4 | 2026-03-30 | HTML escape 추가, send-button polling, chat_url 재사용 |
| v1.4.1 | 2026-03-30 | 오류 대응 표 polling 문구 통일 |
| v1.5 | 2026-03-30 | GPT Evaluator 루틴 추가 |
| v1.6 | 2026-03-30 | 완료 감지 전면 교체 — get_page_text 비교 방식 |
| v1.7 | 2026-03-30 | 입력 방식 교체: native value setter + InputEvent |
| v1.8 | 2026-03-30 | 출력 형식 규칙: 표형식 금지 |
| v1.9 | 2026-03-30 | Step 1.5 미확인 응답 점검 필수화 |
| v2.0 | 2026-03-30 | GPT 보고 순서 강제: commit → push → GPT 전송 |
| v2.1 | 2026-03-30 | Step 5 산출물→GitHub→GPT 검증 루틴 필수화 |
| v2.2 | 2026-03-30 | Step 5 분기/완료보고/오류경로 보완 |
| v2.3 | 2026-03-30 | Step 5-0 GPT 제안 검증 필수화 |
| v2.4 | 2026-04-02 | 코어/참조 분리 설계 |
| v2.5 | 2026-04-07 | Step 4a/4b 분리: critic-reviewer subagent |
| v2.6 | 2026-04-07 | 코어/참조 물리 분리 실행 — REFERENCE.md 신설, SKILL.md 슬림화 |
| v2.7 | 2026-04-09 | `cdp_chat_send.py` 기본 전송 경로 승격, 직접 DOM 전송은 예비 경로로 재배치 |
| v2.8 | 2026-04-10 | `cdp_chat_send.py`에 최신 답변 기대값 확인 옵션 추가, helper가 최신 답변 불일치까지 직접 차단 |
