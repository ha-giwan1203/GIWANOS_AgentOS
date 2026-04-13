---
name: debate-mode
version: v2.8
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v2.8

> 기술 상세(JS 코드, 완료 감지, 오류 대응, 변경 이력)는 `REFERENCE.md` 참조.

## 개요

Claude가 브라우저에서 ChatGPT 화면을 직접 읽고 반자동 토론을 진행한다.

- API 사용 금지 — 브라우저 자동화만
- **승인 없이 자동 진행** — 반박문 작성 후 즉시 전송
- **토론방 자연어는 한국어만 사용**
- 지정 프로젝트방 전용 운영
- 표형식 출력 금지 — 문단형/번호 목록형만

---

## 트리거

- "토론모드", "AI 토론", "GPT랑 토론", "debate-mode"
- "GPT 의견 들어봐", "GPT한테 물어봐", "GPT한테 알려줘"
- "ChatGPT에게 반박해", "토론 시작"

---

## 지정 채팅방

- 프로젝트 URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c-gpt-keulrodeu-eobmu-jadonghwa-toron/project`
- **새 대화 임의 개설 금지** — 기존 대화가 없으면 프로젝트 내에서만 개설

---

## 언어 규칙

- 토론방에 전송하는 질문/반박/검증 요청/완료 보고는 한국어만 사용
- 판정 요청 라벨도 `통과 / 조건부 통과 / 실패`만 사용
- 예외: code block, selector/data-testid, 파일 경로, commit SHA, 에러 원문 최소 인용
- 에러 원문 최소 인용은 `오류 원문:` 또는 `에러 원문:` 라벨 한 줄로만 허용
- GPT가 영어로 답하면 `영어 없이 한국어만으로 다시 정리해줘.`를 1회 요청한 뒤 후속 루프 진행

---

## GPT Evaluator 루틴

트리거: "gpt한테 보고", "gpt한테 알려줘", "gpt 승인 받아", "gpt한테 확인해"

흐름: commit → push 완료 확인 → GPT 채팅방 보고 → 응답 대기 → 판정 추출 → 자동 분기

### 판정 키워드

통과: "즉시 적용", "바로 적용", "적용 권장", "통과", "문제 없습니다", "진행하면 됩니다"
조건부 통과: "조건부 통과", "이 항목만 보정하면 진행", "소규모 보정 후 진행"
보류/실패: "보류", "실패", "재검토", "수정 필요", "문제 있습니다", "권장하지 않습니다"

> 영어 `PASS/FAIL/HOLD` 응답을 받더라도 내부 해석에만 쓰고, 토론방에 보내는 후속 문장은 한국어만 사용한다.

### 자동 분기

- **통과**: 사용자 확인 없이 바로 구현 → commit → push → GPT 최종 보고
- **조건부 통과**: 수정 항목만 반영 → commit → push → GPT 재판정 요청
- **통과+보류 혼재**: 통과 항목만 적용 → 보류는 TASKS.md 기록 → commit → push → GPT 최종 보고
- **보류**: 작업 중단 → 사용자에게 보류 사유 보고 후 대기
- **실패/재검토**: 수정 후 재보고 (최대 2회) → 동일 실패 2회 시 사용자 보고 후 중단

> GPT가 통과 판정 시 "바로 적용할까요?" 같은 확인 질문 **절대 금지**. 바로 실행.

---

## 실행 절차

### Step 1. 탭 준비
1. **항상** `.claude/scripts/cdp/debate_room_detect.py --navigate` 실행
   - 프로젝트 페이지에서 최상단 채팅방을 자동 탐지 → `debate_chat_url` 덮어쓰기 → 해당 방으로 이동
   - 일반 채팅 링크(`/c/` 단독)는 무시 — 프로젝트 ID 포함 URL만 허용
   - 이전 세션의 debate_chat_url 값을 재사용하지 않음 (매 세션 새로 탐지)
2. 스크립트 실패 시 → 수동으로 프로젝트 URL 접속하여 최상단 방 진입
5. 로그 경로 설정: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS`
6. JSON 로그 초기화: `{"session_id":"...","chat_url":"<진입 URL>","turn_number":0}` 저장

> **URL 갱신 정책**: debate_chat_url은 매 세션 시작 시 프로젝트에서 최상단 방으로 자동 갱신된다.
> 이전 세션의 고정 URL에 의존하지 않는다.

### Step 1.8. Selector Smoke Test (필수)
- REFERENCE.md의 Selector Smoke Test JS 실행 → 입력창/응답영역/composer action 존재 확인
- 빈 입력창 상태에서는 `composer-speech-button`만 보여도 정상으로 간주
- 실패 시 토론 중단 + 사용자 보고 (UI 변경 감지)

### Step 1.5. 입력 전 미확인 응답 점검 (필수)
- `[data-message-author-role="assistant"]` 마지막 블록 확인 → 새 응답 있으면 먼저 읽고 반영

### Step 2. 메시지 전송
- 기본 전송 경로: `.claude/scripts/cdp/cdp_chat_send.py --auto-debate-url --mark-send-gate` (상세: REFERENCE.md §1)
- **[FALLBACK]** Chrome MCP type은 CDP 불가 시에만. javascript_tool execCommand+insertText는 send_gate.sh가 차단
- 전송 본문 자연어는 한국어만 작성
- 완료 감지: stop-button polling 또는 get_page_text 비교 (상세: REFERENCE.md §2)
- 응답 읽기: assistant 마지막 블록 innerText (상세: REFERENCE.md §3)

### Step 3. 반박 생성 및 자동 전송
1. GPT 응답 핵심 주장 3줄 요약
2. 반박 포인트 2~3개 도출 (근거 + 대안)
3. Step 1.5 재확인 → **승인 없이** 전송 → 반복

### Step 4a. 종료 판정
- 설정 턴 수 도달 / "합의" 감지 / 동일 주장 2회 반복 시 종료
- 합의안 + 미합의 쟁점 + 즉시 실행안 3개 도출
- 임시 로그 저장 (.md + .json)

### Step 4b. 품질 심층 검토 (critic-reviewer 1회)
1. `critic-reviewer` subagent 호출 — 입력: 토론 로그 .md 경로
2. 4축 평가: 독립성/하네스 엄밀성(필수) + 0건감사/결론 일방성(보조)
3. 판정별 분기:
   - **통과** → Step 5 진행
   - **WARN** → 경고 기록 후 Step 5 진행 (사용자에게 WARN 사유 1줄 보고)
   - **실패** → **Step 5 진행 차단**. 사용자에게 실패 사유 보고 후 대기. 사용자 명시 승인 없이 Step 5로 넘어가지 않는다.
4. 세션당 1회만 (재호출 금지). 결과는 .json `critic_review` 필드에 저장

### Step 5. 산출물 → GitHub → GPT 최종 검증

> Step 4에서 멈추지 않는다. 산출물이 있으면 반드시 이 단계까지 완료.

#### 5-0. GPT 제안·지적 내용 검증 (필수 — 파일 반영/수정 전)
> GPT 제안 반영 또는 GPT 지적(조건부 통과/실패/수정 필요) 대응 시 반드시 수행.
> 검증 없이 GPT 출력을 그대로 적용하거나 GPT 지적을 실물 확인 없이 수용하는 것은 금지.

1. 대상 파일 Read → GPT 항목별 판정(신규/중복/충돌) → 신규만 반영
2. 검증 결과 보고 후 반영 (승인 대기 없음)

#### 5-1. 산출물 저장
#### 5-2. GitHub 커밋 + 푸시 (push 전 GPT 보고 금지)
#### 5-3. GPT 최종 검증 요청 (파일 목록 + 커밋 + 검증 항목)

#### 5-4. GPT 판정에 따른 분기

- **통과**: 루틴 종료 → 사용자 완료 보고
- **조건부 통과**: **Step 5-0 재수행**(지적 파일 Read → 사실 여부 확인 → 맞으면 수정, 틀리면 반론) → 재커밋 → Step 5-3 반복
- **통과+보류 혼재**: 통과 항목은 **Step 5-0 재수행** 후 반영 → 보류는 TASKS.md → 재커밋 → GPT 최종 보고
- **보류**: 사용자 보고 후 대기
- **실패/재검토**: **Step 5-0 재수행** → 수정 후 재보고 (최대 2회)

#### 5-5. 완료 보고 형식
```
완료 보고
- 산출물: [파일/패키지 목록]
- GitHub: [repo URL] / [commit SHA]
- GPT 판정: 통과
- 잔여 이슈: 없음 / [있으면 1줄]
```

---

## 로그

JSON 필수 필드: `session_id`, `chat_url`, `turn_number`, `last_reply_hash`, `turns[]`, `result`, `critic_review`

### 턴별 harness 스키마 (세션15 합의)
```json
{
  "turn": 1,
  "claude": "의제 요약",
  "gpt": "응답 요약",
  "harness": {
    "summary_counts": {"채택": 2, "보류": 1, "버림": 0},
    "채택": [
      {"item": "대상", "label": "실증됨|일반론|환경미스매치|과잉설계", "evidence": "근거 1줄", "ref": "파일:행번호 또는 커밋SHA"}
    ],
    "보류": [],
    "버림": []
  }
}
```

- `summary_counts`: 빠른 스캔용 숫자 요약 (필수)
- `label`: 실증됨 / 일반론 / 환경미스매치 / 과잉설계 중 1개
- `evidence`: 판정 근거 1줄
- `ref`: 파일경로:행번호, 커밋SHA, 로그파일명 중 하나 (없으면 null)
- `result` 섹션도 동일 스키마 적용

오류 대응, JS 코드 상세, 변경 이력 → `REFERENCE.md`
