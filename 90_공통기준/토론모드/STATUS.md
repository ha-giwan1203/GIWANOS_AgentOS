# 토론모드 진행 현황

> 이 파일은 토론모드 하위 도메인의 재개 위치와 운영 메모만 관리한다.
> 저장소 전체 상태 원본은 `90_공통기준/업무관리/TASKS.md`이며, 전역 판정은 업무관리 문서 우선순위를 따른다.

최종 업데이트: 2026-04-11 — 세션15 설계 토론 2건 합의 (C+ fallback 계측 + auto-resolve 분기)

## 현재 상태: 운영 중 (v2.8)

- CLAUDE.md: 코어 규칙 정리 완료 (selector/하네스/금지사항)
- SKILL.md: v2.6 — Step 4a(종료판정)/4b(critic-reviewer) 분리
- REFERENCE.md: 기술 상세 분리 완료 (JS 코드, fallback 체인, 오류 대응)
- Selector smoke test: idle composer 상태(`composer-speech-button`) 허용, 전송 직전 submit button 재확인
- REFERENCE.md 통합 JS: `[data-testid="send-button"], #composer-submit-button` fallback으로 실전 selector와 일치
- 언어 규칙: 토론방 자연어는 한국어만 사용, 판정 요청 라벨도 `통과 / 조건부 통과 / 실패`로 고정
- GPT 전송 경로: Chrome MCP 도구로 통일 (2026-04-13). CDP 스크립트(cdp_chat_send.py)는 사내 시스템 전용
- 기본 전송: Chrome MCP `type` 액션 → 전송 버튼 클릭. javascript_tool execCommand 직접 사용은 send_gate.sh가 차단
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
- 2026-04-09: 토론모드 기본 전송 경로를 `cdp_chat_send.py`로 승격, 직접 DOM 전송은 예비 경로로 재배치
- 2026-04-09: v2.7 버전 표기를 토론모드 기본 전송 경로 승격과 정렬
- 2026-04-09: `cdp_chat_send.py` 에러 원문 예외 정렬
- 2026-04-10: `debate_room_detect.py` 신규 — 매 세션 프로젝트 최상단 방 자동 탐지 + 진입 코드 강제
- 2026-04-10: SKILL.md v2.8 — Step 1에서 `debate_room_detect.py --navigate` 필수 실행으로 변경
