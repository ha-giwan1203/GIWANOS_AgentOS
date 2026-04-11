# 토론모드 코어 규칙

> 앱 운영 기준: `APP_INSTRUCTIONS.md`
> 실행 절차: `debate-mode/SKILL.md`
> 기술 상세: `REFERENCE.md`
> 전역 상태 원본: `../업무관리/TASKS.md`
> 토론모드 내부 작업 목록: `TASKS.md`

> **코어: 이 파일**

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
1. 기존 탭 확인 → 있으면 switch, 없으면 navigate
2. main 영역 JS로 대화 URL 추출 → navigate (클릭 금지)
3. **SEND GATE**: 전송 직전 assistant 최신 텍스트 재읽기 (NEVER — 생략 금지)
4. 기본 전송: `.claude/scripts/cdp/cdp_chat_send.py --auto-debate-url --mark-send-gate` + 직전 최신 답변 100자 기대값 전달
5. **[DEPRECATED]** 직접 DOM 전송(execCommand+insertText)은 deprecated → send_gate.sh가 차단. CDP 기본 경로만 사용
6. stop-button polling 적응형 (3/5/8초, 최대 300초) + 매 주기 사용자 중단 확인
7. 응답 읽기 → 하네스 분석 → 반박 생성 → 전송 → 반복

> 로컬 CDP 스크립트 경로에서는 `.claude/scripts/cdp/cdp_chat_send.py --require-korean --mark-send-gate`를 기본 전송 경로로 사용한다. `--expect-last-snippet` 또는 `--expect-last-snippet-file`로 직전 최신 답변 기대값을 함께 넘겨 화면이 바뀌면 helper가 전송을 차단해야 한다. 직접 DOM 전송은 helper를 쓸 수 없을 때만 예비 경로로 허용한다.

## 고정 Selector (2026-03-31 실증)
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

## GPT 실물 검증 공유 (NEVER)
구현 → `git commit` → `git push` → SHA + `git show --stat` 요약 포함 공유 (한 번에). 커밋 없이 먼저 공유 금지.

## 금지사항
- [NEVER] ChatGPT API 호출
- [NEVER] find()/form_input 입력
- [NEVER] DataTransfer/synthetic paste 입력
- [NEVER] JS 내부 polling (sleep 분리 호출만)
- [NEVER] sleep 60 같은 긴 고정 대기

## 상세 참조
selector 목록, fallback 체인, 오류 대응, 로그 형식, 병행 작업 규칙 → `REFERENCE.md`
