---
name: debate-mode
version: v2.11
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  "3자 토론", "Gemini도 포함", "Claude×GPT×Gemini", "3-party" 언급 시 3자 토론 모드로 전환.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v2.11

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

### 2자 토론 (Claude × GPT) — 기본
- "토론모드", "AI 토론", "GPT랑 토론", "debate-mode"
- "GPT 의견 들어봐", "GPT한테 물어봐", "GPT한테 알려줘"
- "ChatGPT에게 반박해", "토론 시작"

### 3자 토론 (Claude × GPT × Gemini) — 상호 감시
- "3자 토론", "3-party", "3-way", "삼자 토론"
- "Gemini도 포함", "Gemini도 넣어", "Claude×GPT×Gemini"
- "상호 감시", "교차 검증 토론"

> 3자 토론 트리거 감지 시 아래 "3자 토론 모드" 섹션의 루프를 따른다. 기본 절차는 2자 토론과 동일하며, 각 라운드마다 교차 검증 단계가 추가된다.

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

### Step 1. 세션 초기화 (로그만 — 브라우저 조작 금지)
1. 로그 경로 설정: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS`
2. JSON 로그 초기화: `{"session_id":"...","chat_url":"","turn_number":0}` 저장
3. `chat_url`은 첫 gpt-send 호출 후 `.claude/state/debate_chat_url`에서 읽어 갱신

> **[NEVER] debate-mode 안에서 Chrome MCP 도구를 직접 호출하지 않는다.**
> tabs_context_mcp, navigate, javascript_tool, get_page_text, find, computer 등
> 브라우저 조작은 전부 gpt-send/gpt-read 스킬이 내부에서 처리한다.
> 탭 준비, 채팅방 진입, 셀렉터 확인, SEND GATE 모두 gpt-send/gpt-read 책임이다.

### Step 2. 메시지 전송 + 응답 읽기

**[MUST] 모든 브라우저 상호작용은 전용 스킬로만:**
- 전송: `Skill(skill="gpt-send", args="메시지 텍스트")`
- 응답 읽기: `Skill(skill="gpt-read")`
- 전송 본문 자연어는 한국어만 작성
- gpt-send가 탭 준비 → 채팅방 진입 → SEND GATE → 입력 → 전송 → 응답 읽기를 일괄 처리

### Step 3. 반박 생성 및 자동 전송
1. GPT 응답 핵심 주장 3줄 요약
2. 반박 포인트 2~3개 도출 (근거 + 대안)
3. Step 1.5 재확인 → **승인 없이** 전송 → 반복

### Step 3-W. 3자 토론 모드 (3-way — 상호 감시 프로토콜)

> 트리거가 3자 토론일 때만 적용. 2자 토론은 Step 3까지로 종료 판정으로 진행.
> 상위 규칙: `../CLAUDE.md` "상호 감시 프로토콜" 섹션.

#### 원칙 (NEVER 생략)
- 단일 모델 동의만으로 합의 종결 금지
- 최소 2/3 검증 통과 시만 채택
- Claude 단독 설계 결정 금지 — GPT/Gemini 양측 검증 필수
- **3자 토론 맥락에서 `/ask-gemini` (CLI 단발) 사용 금지** — 맥락 단절 방지 (세션67 사용자 결정·Gemini 의견 채택)
- **재라운드 최대 3회** — 동일 의제 3회 내 `pass_ratio ≥ 2/3` 미달 시 "합의 실패" 기록 후 종료 (세션67: 초기 5회 → Gemini 재반박 "3회가 한계점, 5회는 토큰 낭비·논점 이탈" 수용 → 사용자 결정 3회 확정)

#### 도구 통일 (세션67)
3자 토론 내 모델 호출은 전부 **웹 UI 멀티턴**으로만 수행한다:
- GPT: `Skill(skill="gpt-send")` + `Skill(skill="gpt-read")`
- Gemini: `Skill(skill="gemini-send")` + `Skill(skill="gemini-read")`

> `/ask-gemini` (CLI 헤드리스 단발)는 3자 토론 안에서 사용 금지. 용도: WebFetch fallback · 대용량 · 멀티모달 · 토론 외 일반 질의 (본 스킬 밖).

#### 라운드 루프 (매 라운드 6단계)

1. **GPT 답 수령** — `/gpt-send` + `/gpt-read` (토론 맥락 누적되는 동일 채팅방)
2. **GPT 답 → Gemini 1줄 검증**: GPT 원문 전체를 payload로 `/gemini-send`에 동봉 + "다음 GPT 답변에 대해 '동의 / 이의 / 검증 필요' 중 하나로 1줄 답. 근거 1문장 포함" 요청 → `/gemini-read`
3. **Gemini 본론 수령** — `/gemini-send`에 의제 본론 요청 (같은 Gem 채팅방, 맥락 유지) → `/gemini-read`
4. **Gemini 답 → GPT 1줄 검증**: Gemini 원문 전체를 payload로 `/gpt-send`에 동봉 + 동일 1줄 답 요청 → `/gpt-read`
5. **Claude 종합·설계안 작성** → 양측(GPT + Gemini) 채팅방에 설계안 원문 전체 동봉 1줄 검증 요청 → 양측 응답 수신
6. **검증 결과 집계** → `pass_ratio` 계산 (채택 수 / 3) → 2/3 이상 시 채택, 미달 시 재라운드 (단, 누적 3회 초과 금지)

#### 검증 1줄 payload 첨부 강제 (NEVER 생략 — GPT 지적 반영)

교차 검증 요청 시 **검증 대상 원문 전체를 다음 메시지 payload에 반드시 포함한다**:
- "다음 X 답변에 대해 ..." 헤더 + `[X 원문 전체 인용]` + "응답 형식: 동의 / 이의 / 검증 필요 — 근거 1문장"
- 원문 요약·발췌·생략 금지. 모델이 요약본만 보고 검증하면 맥락 손실 발생
- 원문이 너무 긴 경우에도 절삭 금지 — 길이 제한 초과 시 라운드 재설계 (의제 분할)

#### 자동 게이트 (3way 필수 — GPT 지적 반영)

라운드 종료 시 다음을 자동 검사한다:
1. `cross_verification` JSON에 필수 4키 존재: `gpt_verifies_gemini` / `gemini_verifies_gpt` / `gpt_verifies_claude` / `gemini_verifies_claude`
2. 각 값은 enum `{"동의", "이의", "검증 필요"}` + 근거 1문장
3. `pass_ratio` 수치 계산: 채택 수(동의 개수) / 3 (소수점 2자리) — 수동 입력 금지, Claude가 항상 재계산
4. 하나라도 누락/형식 불일치면 **즉시 중단 → 사용자 보고 → 해당 라운드 재실행** (누적 3회 카운트에 포함)

> 자동 게이트 스크립트 구현은 별건 안건: TASKS "3way cross_verification 자동 게이트 스크립트" 참조.

#### 로그 파일 구조
- 3자 토론 로그: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS_3way/`
- 라운드별 파일: `round{N}_gpt.md`, `round{N}_gemini.md`, `round{N}_cross_verify.md`, `round{N}_claude_synthesis.md`
- 누적 3회 도달 시 `consensus_failure.md` 기록 (주제·시도 요약·각 라운드 pass_ratio)

### Step 4a. 종료 판정
- 설정 턴 수 도달 / "합의" 감지 / 동일 주장 2회 반복 시 종료
- **3way 모드**:
  - 최종 합의안도 `cross_verification.pass_ratio ≥ 2/3` 조건 충족해야 채택
  - 미달 시 재라운드 — 단, **동일 의제 누적 3회 초과 금지**
  - 3회 도달 시 "합의 실패" 판정 → `consensus_failure.md` 작성 후 종료 → 사용자에게 실패 사유·각 라운드 pass_ratio 보고
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

### 턴별 harness 스키마 (세션15 합의, 세션66 3자 필드 추가)
```json
{
  "turn": 1,
  "mode": "2way|3way",
  "claude": "의제 요약",
  "gpt": "응답 요약",
  "gemini": "응답 요약 (3way일 때만)",
  "harness": {
    "summary_counts": {"채택": 2, "보류": 1, "버림": 0},
    "채택": [
      {"item": "대상", "label": "실증됨|일반론|환경미스매치|과잉설계", "evidence": "근거 1줄", "ref": "파일:행번호 또는 커밋SHA"}
    ],
    "보류": [],
    "버림": []
  },
  "cross_verification": {
    "gpt_verifies_gemini": {"verdict": "동의|이의|검증 필요", "reason": "근거 1문장"},
    "gemini_verifies_gpt": {"verdict": "동의|이의|검증 필요", "reason": "근거 1문장"},
    "gpt_verifies_claude": {"verdict": "동의|이의|검증 필요", "reason": "근거 1문장"},
    "gemini_verifies_claude": {"verdict": "동의|이의|검증 필요", "reason": "근거 1문장"},
    "pass_ratio_numeric": 0.67,
    "round_count": 1,
    "max_rounds": 3
  }
}
```

- `mode`: `2way` 기본, `3way` 는 3자 토론 트리거 감지 시
- `summary_counts`: 빠른 스캔용 숫자 요약 (필수)
- `label`: 실증됨 / 일반론 / 환경미스매치 / 과잉설계 중 1개
- `evidence`: 판정 근거 1줄
- `ref`: 파일경로:행번호, 커밋SHA, 로그파일명 중 하나 (없으면 null)
- `cross_verification`: **3way 필수**. 4개 검증 필드 각각 `verdict` + `reason` 객체. 2way는 섹션 자체 생략 가능
- `verdict` enum: `"동의" | "이의" | "검증 필요"` 중 하나 — Step 3-W "자동 게이트"에서 검증
- `pass_ratio_numeric`: `"동의" 개수 / 3` (소수 2자리). 0.67 이상 시 채택, 미만 시 재라운드 (단 `round_count < max_rounds`)
- `round_count`: 동일 의제 누적 라운드 수 (1부터 시작)
- `max_rounds`: 기본 3. `round_count >= max_rounds` 도달 시 "합의 실패" 판정
- `result` 섹션도 동일 스키마 적용

오류 대응, JS 코드 상세, 변경 이력 → `REFERENCE.md`
