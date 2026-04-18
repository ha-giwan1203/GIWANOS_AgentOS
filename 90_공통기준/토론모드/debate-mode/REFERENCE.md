# 토론모드 상세 참조 (REFERENCE.md)

> SKILL.md 코어에서 분리된 기술 상세. 실행 중 필요 시 참조.
> 앱 운영 규칙과 문서 우선순위는 상위 `../CLAUDE.md`, `../APP_INSTRUCTIONS.md`를 따른다.
> 토론방에 보내는 자연어 본문은 한국어만 사용한다. 예외: code block, selector/data-testid, 파일 경로, commit SHA 같은 literal, 그리고 `오류 원문:`/`에러 원문:` 라벨 1줄 인용.

> GPT 대화 기본 전송은 `javascript_tool` + `insertText`를 사용한다. CDP 스크립트·`type`·`form_input` 전부 금지 (세션32 확정).

---

## 1. 기본 전송 경로 (v3.0 — javascript_tool + insertText)

```javascript
// 표준 입력 패턴
const ta = document.querySelector('#prompt-textarea');
ta.focus();
document.execCommand('insertText', false, text);
```

전송:
```
1. javascript_tool → 위 코드로 텍스트 삽입
2. find(query="send button") → 전송버튼 ref 획득
3. computer(action="left_click", ref=<ref>) → 전송
```

- submit selector: `[data-testid="send-button"]`, `#composer-submit-button` fallback
- SEND GATE: 전송 직전 `get_page_text`로 assistant 최신 텍스트 재읽기 필수
- 빈 입력창에서는 `composer-speech-button`만 보일 수 있으므로, submit button 재확인은 `insertText` 이후에 수행

### 금지된 입력 방식
- `type` 액션: 느림, 줄바꿈 퇴보
- `form_input`: 줄바꿸 불가
- CDP 스크립트 (`cdp_chat_send.py` 등): 세션32에서 전체 폐기

> **v3.0 변경** (세션32): CDP 폐기 + Chrome MCP 단일화. `javascript_tool + insertText`가 유일한 기본 전송 경로.
> **v2.8 이전**: CDP `cdp_chat_send.py` 기반. 아카이브: `98_아카이브/정리대기_20260413/cdp_scripts/`

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
| v2.9 | 2026-04-18 | 3자 토론 모드(Claude×GPT×Gemini) Step 3-W 신설 + 상호 감시 프로토콜 반영 + 하네스 `cross_verification` 필드 추가 + 종료 판정에 `pass_ratio ≥ 2/3` 조건 추가 |
| v2.10 | 2026-04-18 | 세션67 3자 공유 조건부 통과 대응: ①3자 맥락에서 `/ask-gemini` 사용 금지(웹 UI 멀티턴 단일화) ②검증 1줄 payload 첨부 강제(원문 전체 동봉) ③자동 게이트(enum 검증 + `pass_ratio_numeric` 계산) ④재라운드 최대 5회(`max_rounds`) + 합의 실패 시 `consensus_failure.md` ⑤하네스 `cross_verification` 구조 객체화(`verdict`+`reason`) |
| v2.11 | 2026-04-18 | 세션67 v2.10 재검증 Gemini 반박 수용: `max_rounds` 5 → 3 (토큰 낭비·논점 이탈·억지 타협 우려, 사용자 결정). 자동 게이트 규정·payload 첨부·단일 멀티턴은 v2.10 유지 |
