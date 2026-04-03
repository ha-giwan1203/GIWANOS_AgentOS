# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-04 — hooks 안정화 + I/O 테스트 40/40 (e563f3c1)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 세션 작업 목적

도메인 지시문 미읽기 근본 해결 — phase guard 구현 + 규칙 완화·등급제 (GPT 합의 4턴)

---

## 2. 실제 변경 사항

| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| prompt_inject.sh | v2: sys.argv→stdin 파이프 (cp949 인코딩 버그 수정) | 완료 (211ab177) |
| domain_guard.sh | v3.1: 동일 인코딩 수정 | 완료 (211ab177) |
| domain_read_tracker.sh | v2.1: 동일 인코딩 수정 | 완료 (211ab177) |
| 토론모드 ENTRY.md | Primary 문서로 재작성 — NEVER 등급만, 25줄 | 완료 |
| 토론모드 CLAUDE.md | Reference 격하 + [NEVER]/[SHOULD]/[MAY] 등급 태그 | 완료 |
| domain_guard_config.yaml | keyword_combos 11패턴 + phases 3단 | 완료 |

---

## 3. 미해결 / 다음 AI 액션

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| ~~중~~ | ~~루트 CLAUDE.md + rules 등급 태그~~ | GPT 합의: 현행 유지, 추가 작업 불필요 (원칙형 문서에 태그는 노이즈) |
| ~~중~~ | ~~다른 도메인 phase guard 확장~~ | GPT 합의: 현행 유지, 문서 1개 도메인에 순서 강제 불필요 (재논의 조건: ENTRY.md 신규 생성 시) |
| 낮 | PPT 확장 검증 | Graphviz 다이어그램, visualize 자동 분기 |
