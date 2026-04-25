# 토론모드 코어 규칙

> 앱 운영 기준: `APP_INSTRUCTIONS.md`
> 실행 절차: `debate-mode/SKILL.md`
> 기술 상세: `REFERENCE.md`
> 전역 상태 원본: `../업무관리/TASKS.md`
> 토론모드 내부 작업 목록: `TASKS.md`

> **코어: 이 파일**

## 진입점
**[MUST] 토론/공동작업/공유 관련 요청 시 반드시 `/debate-mode` 스킬로 진입한다.**
- 2자 토론 트리거: "토론", "토론모드", "GPT와 토론", "debate-mode", "공동작업", "공유"
- **3자 토론 트리거**: "3자 토론", "삼자 토론", "3-way", "3-party", "Claude×GPT×Gemini", "Gemini도 포함", "상호 감시", "교차 검증 토론"
- `Skill(skill="debate-mode")` 호출 — 수동 navigate/gpt-send 사용 금지
- navigate_gate 훅이 CLAUDE.md 미읽기 시 ChatGPT 진입을 차단한다

## 목적
Claude가 브라우저에서 ChatGPT 화면을 직접 읽고 반자동 토론을 이어가는 코워크 구조.
- [NEVER] API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만
- [NEVER] 사용자 중간 승인 요청 금지 (예외: 입력값 부족 / 비가역 / "검토만" 지시)
- [NEVER] 토론방에 전송하는 자연어는 한국어만 사용

## 지정 채팅방
- 프로젝트 URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c-gpt-keulrodeu-eobmu-jadonghwa-toron/project`
- [NEVER] 프로젝트방 외 새 대화 개설 금지
- [MUST] 매 세션 시작 시 프로젝트 URL에서 최상단(최신) 채팅방을 자동 탐지하여 `debate_chat_url` 갱신
- [NEVER] 이전 세션의 debate_chat_url 값을 검증 없이 재사용 금지
- [NEVER] 일반 채팅 URL(`/c/` 단독)을 프로젝트 채팅방으로 사용 금지 — 프로젝트 slug 포함 URL만 허용

## 실행 루프
1. **토론 로직만 담당**: 독립 점검 → 하네스 분석 → 반박 생성 → 로그 기록
2. **전송**: `Skill(skill="gpt-send", args="메시지")` — 탭 준비/진입/SEND GATE/입력/전송/응답읽기 일괄
3. **응답 읽기**: `Skill(skill="gpt-read")` — 응답 완료 확인 + 최신 텍스트 반환
4. 하네스 분석 → 반박 생성 → gpt-send → 반복

> **[NEVER] debate-mode 안에서 Chrome MCP 도구 직접 호출 금지.**
> claude-in-chrome 계열(tabs_context_mcp, navigate, javascript_tool, get_page_text, find, computer)
> 및 chrome-devtools-mcp 계열(list_pages, select_page, navigate_page, evaluate_script, click, fill 등)
> 모두 debate-mode에서 직접 호출 금지. 브라우저 조작은 전부 gpt-send/gpt-read/gemini-send/gemini-read 내부에서 처리한다.
> (세션105 스킬 내부는 chrome-devtools-mcp 기반으로 전환됨)

## 고정 Selector (gpt-send/gpt-read 내부 참조용)
```
입력창:      #prompt-textarea              (contenteditable DIV)
전송버튼:    [data-testid="send-button"]   (텍스트 입력 후 표시될 수 있음)
대체확인:    #composer-submit-button       (동일 버튼 id)
idle 상태:   [data-testid="composer-speech-button"]  (빈 입력창에서 허용)
중지버튼:    [data-testid="stop-button"]   (응답 중에만 존재)
응답 노드:   [data-message-author-role="assistant"]
```

## 언어 규칙
- [NEVER] 질문/반박/검증 요청/완료 보고/재판정 요청을 영어 문장으로 보내지 않는다.
- [ALLOW] code block, selector/data-testid, 파일 경로, commit SHA, 에러 원문 최소 인용만 literal 유지 가능
- [ALLOW] 에러 원문 최소 인용은 `오류 원문:` 또는 `에러 원문:` 라벨 1줄로 제한
- [SHOULD] GPT가 영어로 답하면 `영어 없이 한국어만으로 다시 정리해줘.`를 1회 요청한 뒤 계속 진행

## 하네스 분석 (NEVER — 생략 금지)
GPT 응답 → 주장 2~4개 분해 → 라벨링(실증됨/일반론/환경미스매치/과잉설계) → 채택/보류/버림
- 반박문 첫 문단에 `채택:` `보류:` `버림:` 필수
- 사용자 보고는 1줄 요약: `채택 N건 / 보류 N건 / 버림 N건`

## 상호 감시 프로토콜 (3자 토론 시 — NEVER 생략)

3자 토론(Claude × GPT × Gemini) 시 **단일 모델 단독 통과 금지**. 세션66 사용자 지적으로 신설.

**라운드별 교차 검증 강제**:
1. GPT 답 → 다음 메시지에 Gemini의 1줄 검증 첨부 ("동의 / 이의 / 검증 필요")
2. Gemini 답 → 다음 메시지에 GPT의 1줄 검증 첨부
3. Claude 종합·설계 → 양측의 1줄 검증 받은 후 채택
4. 단일 모델 동의로 합의 종결 금지 — 최소 2/3 검증 통과 시만 채택
5. Claude 단독 설계 결정 금지 — GPT/Gemini가 Claude 설계 반박 의무

**검증 누락 시**: 즉시 중단 + 사용자 보고 + 라운드 재실행

**왜 필요**: Claude 단독 검증자 구조는 Claude 검증 누락 시 통과되는 결함. 세션66 5라운드에서 실제 발생. 자세한 배경: 메모리 `project_three_tool_workflow.md` "상호 감시 프로토콜" 섹션

## 자동 승격 트리거 (세션78 실증 후 신설 — NEVER 생략)

2자 토론·공유 루프(`/share-result` 포함)에서 명시 트리거가 "3자"가 아니어도, 응답 내용이 아래 조건 중 하나라도 해당하면 **자동으로 3자 토론 승격**. Claude 단독 판단으로 즉시 반영 금지.

**승격 조건 (B 분류)** — 하나라도 해당 시 (A안-1 2026-04-20 엄격화: "실행 흐름·판정 변경"만)
- 지적·제안 대상이 `.claude/hooks/*.sh` 또는 `.claude/settings*.json` **이고 실행 흐름·판정 분기·차단 정책이 바뀌는 경우** (로그 메시지·timing 지표 추가만이면 A 분류)
- 게이트·정책·훅의 재배치·신설·삭제·분기 로직 변경 **(실행 흐름·판정을 바꾸지 않는 단순 로그·timing·주석 추가는 제외)**
- `has_any_req`/`early-exit`/`commit-push 검증` 등 훅 흐름 재구성
- 파이프라인 단계·Policy·규칙 재정의 (map_scope·skill_read·tasks_handoff 등 evidence 정책 포함)
- 외부 인터페이스(ERP/MES/스프레드시트 양식) 영향
- smoke_test 커버리지 추가가 구조 변경과 세트로 묶인 경우 (단순 케이스 추가는 제외)
- **스킬 md의 Step 절차 분기 신설·삭제** (예: 1-Z 같은 새 단계 추가 — D안 선례)

**즉시 반영 허용 (A 분류)** — 2자 종결 경로 유지 (A안-1 2026-04-20 확장)
- 문서 오타·드리프트 정정 (TASKS/HANDOFF/STATUS 내용 수정)
- 단일 값·수치 조정 (임계값·상수·주석 문구)
- 명백한 버그 수정 (실행 실패 원인 명확)
- smoke_test 케이스 단순 추가 (기존 로직 검증만)
- 도메인 데이터·스프레드시트 수정
- **훅 내 로그 메시지·timing 지표·주석 추가·개선** (실행 흐름 미변경)
- **스킬 md의 주석·경고 문구·설명 추가** (Step 절차 단계 미변경)
- **사용자가 명시적으로 3자 승격을 중단·거부하고 직접 구현을 지시한 작업** (아래 "사용자 지시 예외" 참조)

**사용자 지시 예외 (D안 2026-04-20 선례 — 신설)**:
B 분류에 해당하는 구조 변경이라도, 세션 내에서 사용자가 **명시적으로 3자 토론 승격을 중단·거부하고 직접 구현 경로를 지시**한 경우 해당 지시 범위 한정 A 분류로 강등 허용.

- **조건**: "이 경로로 가자" / "토론 중단" / 특정 안 지정 등 명시 지시 + 중단/거부 의사 확인. 묵시적 동의·유추 금지.
- **기록 필수**: 커밋 메시지에 `사용자 지시 예외` 명기 + 중단 경위 로그 파일 링크
- **선례**: `90_공통기준/토론모드/logs/debate_20260420_163810_3way/abort.md` (D안 스킬 진입 세션캐시, 커밋 `ed0ba225`)
- **범위 제한**: 예외는 해당 지시 1건 한정. 연관 변경·후속 작업에 자동 확대 금지. 새 의제는 다시 B/A 판정.

**적용 방식**:
1. `/share-result` 5단계 응답 하네스 또는 2자 토론 응답 하네스 단계에서 위 조건 판별
2. B 분류 시 `Skill(skill="debate-mode", args="...")` 호출로 승격 (3-way 루프 재개)
3. A 분류 시 기존 2자 흐름 유지 (즉시 반영 + 재커밋)
4. 사용자 지시 예외 적용 시 커밋 메시지에 예외 근거 명기 + 다음 새 의제는 다시 B/A 판정

**왜 필요 (실증)**:
- 세션78: 공유 루프에서 GPT FAIL 판정(evidence_gate `has_any_req` 재배치 + push-only 분기)을 수령한 뒤 Claude가 Gemini 교차 검증 없이 단독 반영 시도 → 사용자 지적 "토론모드 작동 안 했다" → 철회. 단일 모델 단독 통과 금지 원칙이 "3자 토론" 명시 트리거에만 적용되던 구조적 허점 해소.
- 세션84(2026-04-20): "토론모드가 느리다"는 의제 자체를 3자 토론으로 승격했으나 **토론 진입 단계에서 사용자가 병목을 실시간 체감** → 토론 중단·D안 직접 구현 지시. B 분류 규칙이 너무 광범위해 "저위험 개선조차 3자로 올라감" 역설 드러남. A 분류 확장 + 사용자 지시 예외 조항 신설로 규칙 자체를 합리화.

**[NEVER]** 사용자 지시 예외 외에 B 분류를 A로 낮춰 Claude가 단독 수정 반영 금지. B/A 판정이 모호하면 기본 B로 간주(안전측)하고 승격한다.

**관련 규정**: `.claude/commands/share-result.md` 5단계, 메모리 `feedback_structural_change_auto_three_way.md`.

## 백그라운드 탭 Throttling 대응 (세션70 실증, 세션105 CDP 네이티브 전환 — NEVER 생략)

**증상**: Chrome은 백그라운드 탭의 JavaScript 타이머·네트워크·DOM 업데이트를 throttling한다. ChatGPT/Gemini 탭이 백그라운드일 때 응답 DOM 생성이 지연되거나 누락되어 감지 실패가 발생한다. 세션69 Gemini synthesis 미수령 원인이 이것이었다.

**대응 (세션105 CDP 네이티브 — 필수)**:
1. **전송/읽기 직전 대상 페이지 활성화**: `mcp__chrome-devtools-mcp__select_page(pageId, bringToFront=true)`가 CDP `Target.activateTarget`을 직접 호출해 탭을 foreground로 올린다. URL 재진입 불필요, 페이지 상태 완전 보존.
2. 기존 claude-in-chrome 경로(`navigate(url, tabId)` 재호출 hack)는 폐기. chrome-devtools-mcp는 CDP 네이티브 activate API 제공.
3. 응답 감지 적응형 polling(3/5/8초, 최대 300초)에서 stop-button·aria-disabled 상태 변화를 감지 못 하면 **`navigate_page(type="reload")` 1회 재시도** 후 다시 polling.
4. 2회 연속 감지 실패 시 "탭 throttling 복구 실패 — 사용자 수동 활성화 필요" 보고.

**3자 토론 특이사항**:
- 양측 모델(GPT·Gemini) 중 한쪽은 항상 백그라운드가 된다.
- 매 전송/읽기 전 `select_page(bringToFront=true)` 필수. 병렬 폴링 금지(백그라운드 쪽 필연 지연).
- GPT 전송 → GPT 수신 → Gemini `select_page` → Gemini 전송 → Gemini 수신 순으로 직렬 실행.

**CDP Chrome 단독 사용 (세션107 사용자 지시 — NEVER 생략)**:

> 2자 / 3자 토론모드는 **CDP Chrome 단독 사용**만 허용. 사용자 명시 정책(2026-04-25 세션107).

- **[NEVER]** 일반 Chrome 프로필(기본 사용자 프로필)에서 토론모드 진입 금지
- **[NEVER]** claude-in-chrome 계열 MCP(`mcp__Claude_in_Chrome__*`) 토론모드 내 사용 금지 — chrome-devtools-mcp 단독 경로
- **[NEVER]** CDP Chrome 미기동 상태에서 토론 시작 금지 — 즉시 실패 보고
- **[MUST]** 토론 진입 전 CDP 연결 확인: `curl -s http://127.0.0.1:9222/json/version` 200 응답 필수
- **[MUST]** 별도 프로필 `C:\temp\chrome-cdp` 만 사용. 다른 user-data-dir 금지

**전제 조건 (기존)**:
- Chrome M136+에서 기본 프로필은 `--remote-debugging-port` 사용 금지 (쿠키 탈취 방어).
- 토론모드는 반드시 **별도 프로필** (`C:\temp\chrome-cdp`)에서 `--remote-debugging-port=9222`로 기동.
- **[NEVER 생략]** `--remote-debugging-address=127.0.0.1` 플래그 필수 — 누락 시 Windows Chrome이 IPv6 `::1`에만 바인딩하여 chrome-devtools-mcp가 127.0.0.1:9222 fetch 실패. 세션105 Round 2 실증.
- 기본 Chrome과 CDP Chrome 병행 기동 가능 (CDP는 별도 프로필이므로 충돌 없음). chrome-devtools-mcp는 CDP 포트 9222에만 연결.
- **정식 launch 커맨드**:
  ```powershell
  Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--remote-debugging-address=127.0.0.1','--user-data-dir=C:\temp\chrome-cdp'
  ```
- **종료 시 주의**: `taskkill //F`로 강제 종료하면 쿠키 DB 미플러시로 로그인 세션 소실. 창 정상 닫기 권장.

**관련 스킬**: `/gpt-send`, `/gpt-read`, `/gemini-send`, `/gemini-read` 모두 chrome-devtools-mcp 기반. 모든 Step 1-C에 `select_page(bringToFront=true)` 단계 명시. claude-in-chrome 계열 MCP 호출 금지.

## GPT 실물 검증 공유 (NEVER)
구현 → `git commit` → `git push` → SHA + `git show --stat` 요약 포함 공유 (한 번에). 커밋 없이 먼저 공유 금지.

## 금지사항
- [NEVER] ChatGPT API 호출 — **예외 1건**: Step 6-2/6-4 단발 교차 검증(β안-C, 세션85 3자 만장일치). 아래 "β안-C 예외" 섹션 참조
- [NEVER] DataTransfer/synthetic paste 입력
- [NEVER] JS 내부 polling (sleep 분리 호출만)
- [NEVER] sleep 60 같은 긴 고정 대기
- [NEVER] CDP 스크립트 사용 (cdp_chat_send.py 등 — 폐기됨)

## β안-C 예외 — 단발 교차 검증 API 허용 (세션85 3자 만장일치, 2026-04-20)

> 배경: debate_20260420_190020_beta_3way/ pass_ratio=1.0. `[NEVER] API 호출`의 **유일 예외**. 범위 확대 금지.

**허용 범위 (이것만)**:
- `debate-mode/SKILL.md` Step 6-2 (Gemini→GPT 1줄 검증)
- `debate-mode/SKILL.md` Step 6-4 (GPT→Gemini 1줄 검증)

**필수 조건 (모두 만족 시에만 활성)**:
1. **원문 payload 동봉**: 검증 대상 원문 전체 + 판정 기준 프롬프트 포함. 요약·발췌·절삭 금지
2. **병렬 실행**: 6-2와 6-4를 API 병렬 호출 (순차 대비 추가 감축)
3. **모델 매칭**: 본론 웹 UI 모델과 동일 프로바이더 API 사용 — OpenAI↔OpenAI, Google↔Google. 드리프트 최소화
4. **실패 fallback**: API 실패 시 1회 재시도 후 기존 웹 UI 경로 자동 복귀
5. **로그 브릿지**: 6-5 Claude 종합 시작 전 `cross_verification` JSON을 웹 UI 프롬프트로 **원문 주입**. `logs/debate_*/roundN_cross_verification.{md,json}` 이중 기록
6. **키 관리**: 세션별 발급·종료 시 revoke, OpenAI/Gemini 월별 예산 상한 설정
7. **모델 버전 로그 고정**: 드리프트 추적 가능하도록 호출 시 model_id 로그 기록

**[NEVER] 확대 금지**:
- 본론(Step 6-1, 6-3) API 전환 금지 — 웹 UI 멀티턴 유지
- 종합(Step 6-5) API 전환 금지 — Claude 종합은 웹 UI 프롬프트 기반
- 양측 최종 판정(통과/조건부/실패)은 웹 UI 수령만 인정
- 단발 검증 외 일반 토론 API 호출 금지

**구현 경로** (세션86 완료):
- `90_공통기준/토론모드/openai/openai_debate.py:call_openai_parallel` (require_payload 강제 + ThreadPoolExecutor)
- `90_공통기준/토론모드/gemini/gemini_debate.py:call_gemini_parallel` (단발 검증 모드 신설)
- `90_공통기준/토론모드/bridge/log_bridge.py:write_cross_verification` (JSON 스키마 검증 + md/json 이중 기록)
- `90_공통기준/토론모드/bridge/api_fallback.py:run_with_fallback` (1회 재시도 + rate limit 즉시 fallback)
- 2주 관찰 기간: 구현 후 incident 0건 확인 시 고정 (세션86 착수, 세션87~96 누적)

**로그**: `90_공통기준/토론모드/logs/debate_20260420_190020_beta_3way/round1_final.md`

## 상세 참조
selector 목록, fallback 체인, 오류 대응, 로그 형식, 병행 작업 규칙 → `REFERENCE.md`
