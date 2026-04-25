---
name: debate-mode
version: v2.11
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론", "gpt한테 물어봐", "gpt한테 알려줘" 등을 언급하면 반드시 이 스킬을 사용할 것.
  "3자 토론", "Gemini도 포함", "Claude×GPT×Gemini", "3-party" 언급 시 3자 토론 모드로 전환.
  브라우저 자동화 기반(세션105 chrome-devtools-mcp). 본론·종합은 웹 UI 멀티턴.
  단발 교차 검증 API 허용은 β안-C 예외 1건만 (Step 6-2/6-4, 세션85 3자 만장일치). 상세는 `../CLAUDE.md` "β안-C 예외" 섹션.
  승인 없이 자동 진행.
---

# 토론모드 (debate-mode) 스킬 v2.11

> 기술 상세(JS 코드, 완료 감지, 오류 대응, 변경 이력)는 `REFERENCE.md` 참조.

## 개요

Claude가 브라우저에서 ChatGPT 화면을 직접 읽고 반자동 토론을 진행한다.

- API 사용 원칙 — 브라우저 자동화만. **예외 1건**: Step 6-2/6-4 단발 교차 검증(β안-C, 세션85 3자 만장일치). 본론·종합 API 전환 금지. 상세는 `../CLAUDE.md` "β안-C 예외" 섹션
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
> claude-in-chrome 계열(tabs_context_mcp, navigate, javascript_tool, get_page_text, find, computer)
> 및 chrome-devtools-mcp 계열(list_pages, select_page, navigate_page, evaluate_script, click, fill 등) 모두 직접 호출 금지.
> 브라우저 조작은 전부 gpt-send/gpt-read/gemini-send/gemini-read 스킬이 내부에서 처리한다.
> 탭 준비, 채팅방 진입, 셀렉터 확인, SEND GATE 모두 전용 스킬 책임이다.
> (세션105 스킬 내부는 chrome-devtools-mcp 기반으로 전환됨)

> **[NEVER] 백그라운드 탭 throttling 대응 생략 금지 (세션70 실증, 세션105 CDP 네이티브 전환)**
> gpt-send/gpt-read/gemini-send/gemini-read 내부 Step 1-C 또는 3-prep에
> `mcp__chrome-devtools-mcp__select_page(pageId, bringToFront=true)` 단계 반드시 포함.
> CDP `Target.activateTarget` 네이티브 호출로 탭 foreground 전환. URL 재진입 hack 폐기.
> 3자 토론은 GPT·Gemini 중 한쪽이 항상 백그라운드 → 매 전송/읽기 전 대상 탭 activate.
> 상세: `../CLAUDE.md` "백그라운드 탭 Throttling 대응" 섹션

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

#### 라운드 루프 (매 라운드 7단계 — 세션105 6-0 신설 후)

0. **Claude 독자 답안 선행 작성 (NEVER 생략, 세션105 2026-04-25 신설)**
   - 로그 디렉터리에 `round{N}_claude.md` 파일을 **먼저** 작성
   - 필수 필드: 결론 1줄 / 주장 3~5개 + 라벨(실증됨·일반론·환경미스매치·과잉설계·구현경로미정) + 증거 / 반대 안 예상 약점 / 착수·완료·검증 조건
   - 양측 본론 수령 전 작성 강제 — GPT·Gemini 답변에 종속되지 않은 독립 의견 확보
   - **[NEVER]** round{N}_claude.md 없이 1단계(GPT 전송)로 진입 금지
   - **WHY**: 메모리 `feedback_independent_gpt_review.md` + `feedback_harness_label_required.md` 이행. Round 2 Q1·Q4에서 Claude 답안 선행 없이 양측 답변 축약만으로 "3-way + Claude 축약자" 구조 실증(2026-04-25 사용자 지적). Claude 독자 답안이 없으면 `claude_delta="none"` 마감되어 3-way 기여 실증 불가능
1. **GPT 답 수령** — `/gpt-send` + `/gpt-read` (토론 맥락 누적되는 동일 채팅방)
2. **GPT 답 → Gemini 1줄 검증**: GPT 원문 전체를 payload로 `/gemini-send`에 동봉 + "다음 GPT 답변에 대해 '동의 / 이의 / 검증 필요' 중 하나로 1줄 답. 근거 1문장 포함" 요청 → `/gemini-read`
3. **Gemini 본론 수령** — `/gemini-send`에 의제 본론 요청 (같은 Gem 채팅방, 맥락 유지) → `/gemini-read`
4. **Gemini 답 → GPT 1줄 검증**: Gemini 원문 전체를 payload로 `/gpt-send`에 동봉 + 동일 1줄 답 요청 → `/gpt-read`
5. **Claude 종합·설계안 작성** → 양측(GPT + Gemini) 채팅방에 설계안 원문 전체 동봉 1줄 검증 요청 → 양측 응답 수신
   - 종합안은 **round{N}_claude.md(6-0)와 양측 답변 3건의 4-way 대조 기반**으로 작성
   - claude_delta 계산 — 6-0 독자 답안 대비 최종 종합안의 변화량 (`none`/`partial`/`major`)
6. **검증 결과 집계** → `pass_ratio` 계산 (채택 수 / 3) → 2/3 이상 시 채택, 미달 시 재라운드 (단, 누적 3회 초과 금지)

#### 검증 1줄 payload 첨부 강제 (NEVER 생략 — GPT 지적 반영)

교차 검증 요청 시 **검증 대상 원문 전체를 다음 메시지 payload에 반드시 포함한다**:
- "다음 X 답변에 대해 ..." 헤더 + `[X 원문 전체 인용]` + "응답 형식: 동의 / 이의 / 검증 필요 — 근거 1문장"
- 원문 요약·발췌·생략 금지. 모델이 요약본만 보고 검증하면 맥락 손실 발생
- 원문이 너무 긴 경우에도 절삭 금지 — 길이 제한 초과 시 라운드 재설계 (의제 분할)

#### β안-C — Step 6-2/6-4 단발 검증 API 병렬 전환 (세션85 3자 만장일치, 2026-04-20)

> 배경: `debate_20260420_190020_beta_3way/round1_final.md` pass_ratio=1.0. `[NEVER] API 호출`의 **유일 예외**. 상위 규정: `../CLAUDE.md` "β안-C 예외" 섹션.

**허용 전제 (이것만)** — 웹 UI 본론·종합은 불변:
- Step 6-2 (Gemini→GPT 1줄 검증)와 Step 6-4 (GPT→Gemini 1줄 검증) — API 병렬 호출 허용
- Step 6-1·6-3 본론, 6-5 종합·최종 판정 — 웹 UI 멀티턴 유지

**API 호출 전제 조건** (모두 충족 시 활성, 하나라도 미달 시 웹 UI fallback):
1. 본론(6-1, 6-3) 원문 전체를 payload에 동봉 (요약·발췌·절삭 금지)
2. 6-2/6-4 병렬 실행 (순차 금지 — 속도 이점의 전제)
3. 본론 웹 UI와 동일 프로바이더 API (OpenAI↔OpenAI, Google↔Google)
4. API 실패 시 1회 재시도 → 실패 지속 시 기존 웹 UI 경로 자동 복귀
5. 호출 시 model_id 로그 기록

**로그 브릿지 파이프라인 (Gemini 신규 제안 채택, 필수)**:
- 6-5 Claude 종합 시작 전 아래 JSON을 웹 UI 프롬프트로 **원문 주입**:
```json
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "동의|이의|검증 필요", "reason": "...", "model_id": "..."},
    "gpt_verifies_gemini": {"verdict": "동의|이의|검증 필요", "reason": "...", "model_id": "..."},
    "log_path": "90_공통기준/토론모드/logs/debate_*/roundN_cross_verification.md"
  }
}
```
- 저장 이중화: `logs/debate_*/roundN_cross_verification.{md,json}`
- 주입 누락 시 Claude 종합 착수 금지 (가시 증거 단절 방지)

**실행 모드 분기 (스킬 선택)**:
- **기본값**: 웹 UI 멀티턴 유지 — `/gpt-send`, `/gpt-read`, `/gemini-send`, `/gemini-read` 사용
- **API 모드 (세션86 구현 완료)**:
  - `90_공통기준/토론모드/openai/openai_debate.py:call_openai_parallel` (세션86 리팩터)
  - `90_공통기준/토론모드/gemini/gemini_debate.py:call_gemini_parallel` (세션86 단발 모드 신설)
  - `90_공통기준/토론모드/bridge/log_bridge.py:write_cross_verification` (JSON 스키마 검증 + md/json 이중 기록)
  - `90_공통기준/토론모드/bridge/api_fallback.py:run_with_fallback` (1회 재시도 후 웹 UI 복귀, rate limit 즉시 fallback)
  - 활성 조건: 위 5개 전제 + 7개 보안 조건(`../CLAUDE.md` β안-C 예외 섹션) 모두 만족

**2주 관찰 기간 (API 모드 구현 완료 후)**:
- 구현 고정 전 `logs/debate_*/` 내 incident 0건 확인
- smoke_test 섹션 신설 (최소 5건: 원문 payload 누락 차단, 병렬 실패 fallback, 모델 드리프트 감지, 로그 브릿지 누락 감지, 예산 상한 초과 차단)

**[NEVER]**:
- 본론(6-1, 6-3) API 전환 금지
- 종합(6-5) API 전환 금지 — Claude는 웹 UI 프롬프트 기반만
- 최종 판정(통과/조건부/실패) API 수령 금지
- 병렬 아닌 순차 API 호출 금지 (속도 이점 전제 위반)
- 원문 payload 누락·절삭 금지
- API 실패 시 사용자 보고 없이 무한 재시도 금지 (1회 재시도 후 웹 UI fallback)

**관련 로그**: `90_공통기준/토론모드/logs/debate_20260420_190020_beta_3way/` (Round 1 만장일치, β안-C 합의 원본)

#### 자동 게이트 (3way 필수 — GPT 지적 반영)

라운드 종료 시 다음을 자동 검사한다:
1. `cross_verification` JSON에 필수 4키 존재: `gpt_verifies_gemini` / `gemini_verifies_gpt` / `gpt_verifies_claude` / `gemini_verifies_claude`
2. 각 값은 enum `{"동의", "이의", "검증 필요"}` + 근거 1문장
3. `pass_ratio` 수치 계산: 채택 수(동의 개수) / 3 (소수점 2자리) — 수동 입력 금지, Claude가 항상 재계산
4. 하나라도 누락/형식 불일치면 **즉시 중단 → 사용자 보고 → 해당 라운드 재실행** (누적 3회 카운트에 포함)

> 자동 게이트 스크립트 구현은 별건 안건: TASKS "3way cross_verification 자동 게이트 스크립트" 참조.

#### 6-5 조건부 생략 (A안-2 2026-04-20 3자 토론 만장일치 합의)

> 세션84 3자 토론 `debate_20260420_171419_3way` pass_ratio=1.0. 6-5는 Claude 종합 오해를 잡는 마지막 안전장치이므로 원칙은 유지. 다음 **3조건 + 시스템 제약** 모두 충족 시에만 예외 허용.

**생략 조건 (모두 필수)**:

- **조건 A — 양측 무단서 동의**:
  - 6-2 `gemini_verifies_gpt.verdict == "동의"` AND 6-4 `gpt_verifies_gemini.verdict == "동의"`
  - 두 `reason` 문장에 조건부 단서 키워드 없음: `"단, "`, `"조건부"`, `"추가 확인 필요"`, `"다만"`, `"하지만"`
- **조건 B — Claude 종합안 순수 축약**:
  - 신규 정책/예외/분기/설계 문장 추가 없이 "채택/보류/버림 정리"만
  - 양측 답변의 공통분모를 벗어나는 재해석·범위 확장·표현 변경 금지
  - Claude가 `claude_delta: "none"` self-declare (기계판정 가능한 증적 필드)
- **조건 C — 의제 성격**:
  - 단순 판정형(A 분류: 오타·값·버그·문서 정리·도메인 데이터)
  - 구조·정책·프로토콜 변경(B 분류)이면 **무조건 6-5 유지** — `issue_class` 필드로 기계판정

**시스템 제약 (하드코딩)**:
- `round_count === 1`일 때만 생략 로직 활성. Round 2/3는 자동 생략 불가.
- 이유: Round 2/3은 불일치 누적 맥락이라 Claude 종합 오해 방지 안전장치 필수 (GPT 판정 4 실패 근거)

**생략 시 pass_ratio**:
- 6-2/6-4 두 verdict만으로 계산 (분모 2, 2/3 threshold → 실질 2/2 동의 필요)
- 한쪽이라도 "이의"·"검증 필요"면 생략 불가 → 6-5 수행

**JSON 스키마 확장** (필수 4필드):
```json
{
  "cross_verification": {
    "skip_65": true,
    "skip_65_reason": "양측 무단서 동의 + 순수 축약 + A 분류 + Round 1",
    "claude_delta": "none",
    "issue_class": "A"
  }
}
```

**기록 의무**:
- 생략 시 `round{N}_claude_synthesis.md`에 `skip_65=true` 마킹
- 4 JSON 필드(`skip_65`, `skip_65_reason`, `claude_delta`, `issue_class`) 감사 가능하게 보존
- 생략 안 할 때도 `skip_65: false` + 사유(`claude_delta` 값, `issue_class`) 기록

**[NEVER]**:
- 의제가 B 분류인데 A로 낮춰 생략 금지
- Claude가 `claude_delta="partial"` 또는 `"major"`를 `"none"`으로 낮춰 자체 선언 금지
- Round 2/3에서 수동 생략 시도 금지
- 시스템 제약(`round_count === 1`) 우회 금지

**선례**: 세션84 Round 1 메타 사례 — 본 규정 신설 의제 자체가 B 분류라 `skip_65=false, claude_delta="partial", issue_class="B"`로 6-5 수행, 양측 만장일치 동의(pass_ratio=1.0) 수령 후 반영. 로그: `90_공통기준/토론모드/logs/debate_20260420_171419_3way/`.

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

### Step 5. 산출물 → GitHub → 최종 검증

> Step 4에서 멈추지 않는다. 산출물이 있으면 반드시 이 단계까지 완료.
>
> **[MUST] 3자 토론 모드(3way)에서는 본 Step 전체를 GPT와 Gemini 양측에 동시 수행한다.**
> 단일 모델(GPT 또는 Gemini)에게만 최종 검증을 요청·판정받는 것은 상호 감시 프로토콜 위반이다.
> 2자 토론(2way)에서만 GPT 단독 검증 허용.

#### 5-0. 외부 모델 제안·지적 내용 검증 (필수 — 파일 반영/수정 전)
> GPT/Gemini 제안 반영 또는 지적(조건부 통과/실패/수정 필요) 대응 시 반드시 수행.
> 검증 없이 외부 모델 출력을 그대로 적용하거나 지적을 실물 확인 없이 수용하는 것은 금지.

1. 대상 파일 Read → 항목별 판정(신규/중복/충돌) → 신규만 반영
2. 검증 결과 보고 후 반영 (승인 대기 없음)

#### 5-1. 산출물 저장
#### 5-2. GitHub 커밋 + 푸시 (push 전 외부 모델 보고 금지)

#### 5-3. 최종 검증 요청 (파일 목록 + 커밋 + 검증 항목)
- **2way**: GPT에 `/gpt-send` 1건
- **3way**: GPT와 Gemini에 **양쪽 모두** `/gpt-send` + `/gemini-send` 동시 전송 (순서 무관, 병렬 가능)
- [NEVER] 3way에서 한쪽만 보내고 다른 쪽을 생략하지 않는다

#### 5-4. 판정 분기 (3way는 양측 판정 모두 수령 후 적용)

단일 모델 판정 기준:
- **통과**: 다음 단계 진행
- **조건부 통과**: **Step 5-0 재수행** → 재커밋 → Step 5-3 반복
- **통과+보류 혼재**: 통과 항목 Step 5-0 재수행 → 보류는 TASKS.md → 재커밋 → 최종 보고
- **보류**: 사용자 보고 후 대기
- **실패/재검토**: Step 5-0 재수행 → 수정 후 재보고 (최대 2회)

**3way 종결 조건**:
- 양측 모두 **통과** → 루틴 종료 → 사용자 완료 보고
- 한쪽 조건부/혼재, 다른쪽 통과 → 조건부 항목 Step 5-0 재수행 → 재커밋 → **양측에 재판정 요청**
- 양측 모두 조건부/실패 → Step 5-0 재수행 (우선순위: 공통 지적 > 충돌 지적은 Claude 재종합)
- 한쪽 실패, 다른쪽 통과 → Claude가 실패 근거 실물 검증 → 정당하면 수정 후 양측 재판정, 부당하면 해당 모델에 반론 후 재판정

#### 5-5. 완료 보고 형식
```
완료 보고
- 산출물: [파일/패키지 목록]
- GitHub: [repo URL] / [commit SHA]
- GPT 판정: 통과
- Gemini 판정: 통과   ← 3way일 때 필수
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
    "max_rounds": 3,
    "skip_65": false,
    "skip_65_reason": null,
    "claude_delta": "none|partial|major",
    "issue_class": "A|B|null"
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
