# 토론모드 진행 현황

> 이 파일은 토론모드 하위 도메인의 재개 위치와 운영 메모만 관리한다.
> 저장소 전체 상태 원본은 `90_공통기준/업무관리/TASKS.md`이며, 전역 판정은 업무관리 문서 우선순위를 따른다.

최종 업데이트: 2026-04-15 — 세션48 debate-mode 브라우저 조작 근본 분리 + deny-path 런타임 확장

## 현재 상태: 운영 중 (v2.9)

- CLAUDE.md: 실행 루프 gpt-send/gpt-read 위임 구조로 변경 (세션48)
- SKILL.md: v2.9 — Step 1 Chrome MCP 직접 조작 제거, gpt-send/gpt-read 전면 위임 (세션48)
- ENTRY.md: NEVER 11 추가 — debate-mode 안 Chrome MCP 직접 호출 금지 (세션48)
- REFERENCE.md: 기술 상세 분리 완료 (JS 코드, fallback 체인, 오류 대응)
- Selector smoke test: idle composer 상태(`composer-speech-button`) 허용, 전송 직전 submit button 재확인
- REFERENCE.md 통합 JS: `[data-testid="send-button"], #composer-submit-button` fallback으로 실전 selector와 일치
- 언어 규칙: 토론방 자연어는 한국어만 사용, 판정 요청 라벨도 `통과 / 조건부 통과 / 실패`로 고정
- GPT 전송 경로: `javascript_tool` + `insertText` 기본 (세션32 확정). CDP 폐기됨
- /gpt-send, /gpt-read 명령 추가 (세션34) → 실사용 검증 PASS (세션36)
- 에러 원문 예외: `오류 원문:` / `에러 원문:` 1줄 인용은 한국어 가드 예외로 허용
- incident 수리 루프: `incident_repair.py`가 패치 후보와 검증 단계까지 제안
- 문서 우선순위 정리: 전역 상태는 `../업무관리/TASKS.md`, 토론모드 문서는 하위 도메인용으로 역할 고정
- critic-reviewer subagent: 4축 평가(독립성/하네스 엄밀성 필수 + 0건감사/결론 일방성 보조)
- send_gate.sh: 토론 품질 경량 검사 (반론/대안/독립견해 0건 차단)
- stop_guard.sh: 독립 견해 백스톱 추가
- hooks 연계: `completion_gate` 완료 주장 기반 차단, `incident_repair.py`로 unresolved incident 다음 행동 제안
- 토론방 자동 탐지: `debate_room_detect.py --navigate`로 매 세션 프로젝트 최상단 방 자동 탐지 + 입장 (코드 강제)
- 프로젝트 URL 검증: 프로젝트 ID 없는 일반 `/c/` URL 코드에서 거부
- 실전 테스트: 기존 로그(debate_20260402_토론1.md)로 정상 동작 확인

## 완료 이력
- 2026-03-29: 초기 구축 (폴더, CLAUDE.md, SKILL.md 초안)
- 2026-04-02: 실전 토론 1회 수행
- 2026-04-07: SKILL.md v2.5→v2.6, REFERENCE.md 분리, critic-reviewer 도입, 코어 규칙 리팩터링
- 2026-04-09: 전역 업무관리 문서와의 역할 경계 정리
- 2026-04-09: 새 대화방 시스템 평가 1턴 + idle composer 오탐 제거 + gate 정밀화
- 2026-04-09: GPT `CONDITIONAL PASS` 후속 보정 — submit fallback 정렬 + completion claim 판별식 축소
- 2026-04-09: 토론방 영어 사용 금지 — 한국어 전용 전송 규칙 + 판정 라벨 한국어화
- 2026-04-09: 로컬 CDP helper 추가 + incident 수리 루프 보강
- 2026-04-09: 토론모드 기본 전송 경로를 `cdp_chat_send.py`로 승격 (이후 세션32에서 CDP 폐기)
- 2026-04-10: `debate_room_detect.py` 신규 (이후 세션32에서 CDP 폐기, JS URL 추출로 대체)
- 2026-04-13: 세션32 CDP 전체 폐기 → Chrome MCP 단일화. javascript_tool + insertText 확정
- 2026-04-13: 세션34 /gpt-send, /gpt-read 명령 추가. 토론모드 문서 4개 입력방식 일괄 수정
- 2026-04-15: 세션47 navigate_gate 훅 + 미등록 스킬 12개 등록 + 토론모드 지침 갱신
- 2026-04-15: 세션48 debate-mode 브라우저 조작 근본 분리 (SKILL.md/ENTRY.md/CLAUDE.md). navigate_gate smoke_test 6건 + evidence_gate 런타임 deny 3건 + completion_gate 부분 런타임 1건. smoke_test 162/162 ALL PASS. GPT 재평가 9.4점
