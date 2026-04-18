---
name: debate-mode
version: v2.9
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  "3자 토론", "Gemini도 포함", "Claude×GPT×Gemini", "3-party" 언급 시 3자 토론 모드로 전환.
  API 없이 브라우저 자동화만으로 동작. 승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v2.9

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

#### 라운드 루프
1. **GPT 답 수령** (`Skill(skill="gpt-send", args=의제)` → `gpt-read`)
2. **Gemini 1줄 검증 호출**: `Skill(skill="ask-gemini", args="다음 GPT 답변에 대해 '동의 / 이의 / 검증 필요' 중 하나로 1줄 답. 근거 1문장 포함. GPT 답변: [GPT 원문]")`
3. **Gemini 답(본론) 수령** (`Skill(skill="gemini-send", args=의제)` → `gemini-read`) — 멀티턴 필요 시. 단발 검증이면 2단계로 대체
4. **GPT 1줄 검증 요청**: `Skill(skill="gpt-send", args="다음 Gemini 답변에 대해 '동의 / 이의 / 검증 필요' 중 하나로 1줄 답. 근거 1문장 포함. Gemini 답변: [Gemini 원문]")` → `gpt-read`
5. **Claude 종합·설계안 작성** → 양측(GPT + Gemini)에 1줄 검증 요청
6. 검증 결과 집계 → 2/3 통과 시 채택, 미달 시 재라운드

#### 스킬 선택 기준
| 용도 | 도구 |
|------|------|
| Gemini 빠른 1줄 검증 | `/ask-gemini` (CLI minion, 헤드리스) |
| Gemini 멀티턴 토론 본론 | `/gemini-send` + `/gemini-read` (웹 UI) |
| GPT 토론·검증 | `/gpt-send` + `/gpt-read` |

#### 검증 누락 감지
- 라운드 종료 전 `cross_verification` 필드에 GPT 검증 + Gemini 검증 모두 채워졌는지 확인
- 하나라도 누락이면 **즉시 중단 → 사용자 보고 → 해당 라운드 재실행**
- 누락 상태로 다음 라운드 진행 금지

#### 로그 파일 구조
- 3자 토론 로그: `90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS_3way/`
- 라운드별 파일: `round{N}_gpt.md`, `round{N}_gemini.md`, `round{N}_cross_verify.md`, `round{N}_claude_synthesis.md`

### Step 4a. 종료 판정
- 설정 턴 수 도달 / "합의" 감지 / 동일 주장 2회 반복 시 종료
- **3way 모드**: 최종 합의안도 `cross_verification.pass_ratio ≥ 2/3` 조건 충족해야 채택. 미달 시 재라운드 또는 "합의 실패" 기록
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
    "gpt_verifies_gemini": "동의|이의|검증 필요 — 근거 1줄",
    "gemini_verifies_gpt": "동의|이의|검증 필요 — 근거 1줄",
    "gpt_verifies_claude": "동의|이의|검증 필요 — 근거 1줄",
    "gemini_verifies_claude": "동의|이의|검증 필요 — 근거 1줄",
    "pass_ratio": "2/3 또는 3/3 — 채택 가능 여부"
  }
}
```

- `mode`: `2way` 기본, `3way` 는 3자 토론 트리거 감지 시
- `summary_counts`: 빠른 스캔용 숫자 요약 (필수)
- `label`: 실증됨 / 일반론 / 환경미스매치 / 과잉설계 중 1개
- `evidence`: 판정 근거 1줄
- `ref`: 파일경로:행번호, 커밋SHA, 로그파일명 중 하나 (없으면 null)
- `cross_verification`: **3way 필수**. 누락된 필드 있으면 라운드 재실행 (Step 3-W "검증 누락 감지" 참조). 2way는 섹션 자체 생략 가능
- `pass_ratio`: 2/3 이상 시 채택, 1/3 이하 시 재라운드
- `result` 섹션도 동일 스키마 적용

오류 대응, JS 코드 상세, 변경 이력 → `REFERENCE.md`
