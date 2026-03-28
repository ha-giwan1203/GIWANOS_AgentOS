---
name: debate-mode
description: >
  Claude가 브라우저에서 ChatGPT 웹 화면을 직접 읽고 반박/질문을 생성하여
  반자동 토론을 진행하는 스킬. '토론', '토론모드', 'GPT와 토론', '반박해줘',
  'GPT한테 물어봐', 'GPT 의견 받아와' 등을 언급하면 이 스킬을 사용할 것.
  API 사용 금지, 브라우저 직접 읽기만 사용.
---

# 토론모드 (Debate Mode) v1.2

## 개요
Claude가 ChatGPT 브라우저 화면을 직접 읽고, 반박/질문을 생성하여 입력하는 반자동 토론 시스템.
사용자가 주제와 방향을 결정하고, Claude가 실행한다.

## 실행 모드

| mode | 설명 |
|------|------|
| start | 새 토론 시작. 주제 + 초기 프롬프트 필요 |
| continue | 기존 토론 이어가기. session_id 또는 URL로 식별 |
| review | [v2 예정] 토론 로그 요약/분석 — 현재 미구현 |

## 입력

| 항목 | 필수 | 설명 |
|------|------|------|
| 주제 | ✅ | 토론 주제 |
| 초기 프롬프트 | start 시 | ChatGPT에 보낼 첫 질문 |
| 턴 수 | 선택 | 기본 3턴 |
| 관점 | 선택 | Claude의 입장/역할 (예: 비판자, 현실검증자) |

## 세션 상태 (continue 모드 필수)

continue 모드 진입 시 아래 값을 로그 JSON에서 읽어 복원한다.

| 항목 | 설명 |
|------|------|
| session_id | 토론 시작 시 생성 (YYYYMMDD_HHMMSS) |
| chat_url | ChatGPT 대화 URL (chatgpt.com/c/...) |
| turn_number | 현재 진행 턴 번호 |
| last_reply_hash | 직전 GPT 응답 앞 100자 해시 — 중복 읽기 방지 |

## 실행 절차

### Step 1. 브라우저 준비
- ChatGPT 탭 확인 (없으면 chatgpt.com 열기)
- 로그인 상태 확인
- continue 모드: chat_url로 직접 이동

### Step 2. 프롬프트 입력
- `#prompt-textarea` 찾기
- `innerHTML` 설정 + `InputEvent('input')` 발생
- `KeyboardEvent('keydown', Enter)` 전송

### Step 3. 응답 완료 감지 (2중 조건)
1. **완료 버튼 소멸 확인** (fallback 순서)
   - `button[aria-label="스트리밍 중지"]` 소멸
   - fallback: 전송 버튼(`button[data-testid="send-button"]`) 재활성화
   - fallback2: `[aria-busy="true"]` 요소 소멸
2. `[data-message-author-role="assistant"]` 마지막 블록 **텍스트 자체** 2회 연속 동일 → 완료 판정
- 조건 1만 충족 시 5초 추가 대기 후 조건 2 재확인
- 3회 실패 시 중단

### Step 4. 응답 읽기
우선순위:
1. `document.querySelectorAll('[data-message-author-role="assistant"]')` 마지막 요소 `.markdown` innerText
2. fallback: `read_page` DOM 트리에서 assistant 마지막 블록
3. fallback2: `get_page_text` 전체 추출 후 마지막 "ChatGPT의 말:" 이후 구간

last_reply_hash 비교 — `normalize(full_text)` 전체 해시 기준 (앞 100자 → 전체로 변경)
- 동일하면 응답 미갱신으로 판단, 대기 후 재시도
- 턴별 원문(full_text) 로그 저장 필수 — 해시 충돌 시 원문으로 검증

### Step 5. 반박 생성
- GPT 응답 핵심 주장 요약 (3줄)
- 반박 포인트 2~3개 도출
- "근거 + 대안" 구조로 작성
- 사용자에게 보여주고 승인 대기
- 거절 시 1회 재생성

### Step 6. 반박 입력
- 승인된 반박을 Step 2 방식으로 입력
- 응답 완료 감지 → 읽기 (Step 3~4 반복)

### Step 7. 반복 또는 종료
- 설정된 턴 수까지 Step 5~6 반복
- 종료 시 전체 로그 저장, chat_url 기록

## 로그 저장
- 경로: `90_공통기준/토론모드/logs/`
- 파일명: `debate_YYYYMMDD_HHMMSS.md` + `.json`
- JSON 필수 필드: session_id, chat_url, turn_number, last_reply_hash, turns[]

## 오류 대응

| 상황 | 대응 |
|------|------|
| 응답 미완료 (감지 실패) | 2중 조건 3회 실패 시 중단, 로그 기록 |
| 텍스트 추출 실패 | fallback 순서대로 시도 (Step 4 참고) |
| 로그인 만료 | 사용자에게 재로그인 요청 후 대기 |
| 중복 응답 감지 | last_reply_hash 비교로 재읽기 방지 |
| 반박 거절 | 1회 재생성, 2회 거절 시 사용자에게 직접 입력 요청 |

## 지정 채팅방 원칙 (필수)

**새 ChatGPT 대화를 임의로 개설하지 않는다.**

- 반드시 지정된 프로젝트방을 사용한다:
  - URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
  - 방 이름: `CLAUDE COWORK 업무 자동화 지침만들기`
- 기존 대화가 없으면 해당 프로젝트 내에서 새 대화를 열되, 반드시 위 프로젝트 URL 하위에서만 개설한다
- `chatgpt.com` 루트 또는 일반 대화창(`/c/`)에 임의로 메시지를 보내는 것은 금지
- 맥락 연속성을 위해 이전 대화 URL(chat_url)을 session 상태에 저장하고 재사용한다

## 금지사항
- ChatGPT API 사용
- 자동 로그인
- 사용자 승인 없이 반박 입력
- 이전 로그 덮어쓰기
- 지정 프로젝트방 외부에서 임의로 새 대화 개설

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-28 | 초안 작성 |
| v1.1 | 2026-03-29 | Claude adversarial-review + GPT 검토 반영: 응답 완료 2중 감지, 파싱 우선순위 명시, continue 세션 상태 추가, review 모드 v2 예정 표시, 반박 거절 재생성 절차 추가 |
| v1.2 | 2026-03-29 | GPT 2차 검토 반영: 완료 감지 fallback 3단계 추가(aria-label→send버튼→aria-busy), 텍스트 길이→텍스트 자체 동일 비교, last_reply_hash 앞100자→전체 해시, 턴별 원문 로그 저장 명시 |
