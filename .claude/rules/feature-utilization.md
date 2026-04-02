# 기능 활용 규칙 (GPT 합의 2026-04-02)

## 커스텀 슬래시 명령 (최우선)
반복 절차는 `.claude/commands/` 슬래시 명령으로 캡슐화한다.
제작 우선순위: `/sp3-verify` → `/mes-check` → `/release-proof` → `/debate-run`

## 커넥터 (Notion·Slack·Gmail·Calendar) 활용
커넥터는 독립 호출이 아니라 슬래시 명령 내부에 포함한다.
예: `/sp3-verify` 안에서 Notion 상태 갱신, Slack 결과 알림을 한 번에 처리.

## Context7 사용 범위
Claude Code·MCP 문법 변경 확인 시에만 사용한다.
일반 업무 자동화에서는 호출하지 않는다.

## 병렬 작업
자동 트리거 불가 (Claude Code에 "GPT 대기 진입" hook 이벤트 없음).
사용자 지시 기반 반자동 확정: 사용자가 병렬 대상을 명시하면 background Agent로 실행.

## IDE 연동
현재 보류. 브라우저 기반 워크플로우와 중복되어 실익 불명확.
