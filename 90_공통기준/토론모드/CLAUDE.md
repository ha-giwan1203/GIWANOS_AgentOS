# 토론모드 코어 규칙

> 앱 운영 기준: `APP_INSTRUCTIONS.md`
> 실행 절차: `debate-mode/SKILL.md`
> 기술 상세: `REFERENCE.md`

> **코어: 이 파일**

## 목적
Claude가 브라우저에서 ChatGPT 화면을 직접 읽고 반자동 토론을 이어가는 코워크 구조.
- [NEVER] API 사용 금지 — 브라우저 화면 텍스트 직접 읽기만
- [NEVER] 사용자 중간 승인 요청 금지 (예외: 입력값 부족 / 비가역 / "검토만" 지시)

## 지정 채팅방
- 프로젝트 URL: `https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c/`
- [NEVER] 프로젝트방 외 새 대화 개설 금지
- [NEVER] `.claude/state/debate_chat_url`에 URL이 있으면 다른 대화방 진입 금지 — 해당 URL 필수 사용
- [SHOULD] debate_chat_url 없을 때만 첫 번째(최상단) 대화방에 진입

## 실행 루프
1. 기존 탭 확인 → 있으면 switch, 없으면 navigate
2. main 영역 JS로 대화 URL 추출 → navigate (클릭 금지)
3. **SEND GATE**: 전송 직전 assistant 최신 텍스트 재읽기 (NEVER — 생략 금지)
4. `#prompt-textarea` + `execCommand('insertText')` + `send-button` JS 클릭
5. stop-button polling 적응형 (3/5/8초, 최대 300초) + 매 주기 사용자 중단 확인
6. 응답 읽기 → 하네스 분석 → 반박 생성 → 전송 → 반복

## 고정 Selector (2026-03-31 실증)
```
입력창:      #prompt-textarea              (contenteditable DIV)
전송버튼:    [data-testid="send-button"]
중지버튼:    [data-testid="stop-button"]   (응답 중에만 존재)
응답 노드:   [data-message-author-role="assistant"]
```

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
