# 의제: evidence_gate 예외 규칙 — 로그 단독 diff 전치 조건 추가 건

- 세션: 86
- 모드: 2자 토론 (Claude × GPT)
- 일시: 2026-04-20 22:55 KST
- 로그: `90_공통기준/토론모드/logs/debate_20260420_225550/`

## 배경

`.claude/incident_ledger.jsonl`은 Git 추적 감사 로그(세션15 정책). 매 세션 append 발생 → stop-hook-git-check가 uncommitted 감지 → 커밋 → evidence_gate가 "TASKS.md/HANDOFF.md 갱신 흔적 없음" deny 로그 추가 → 또 uncommitted → 무한 루프.

세션85 incident_audit 보고서(`90_공통기준/업무관리/incident_audit_20260420_session85.md`) 상위 5종 중 #5 패턴(tasks_handoff.req 65건)이 오늘 3회 연속 재생산됨(`d872e62`, `a143b2a`, `2767ba2`). Step 1에서 `skill_usage.jsonl`은 이미 Git 추적 해제(`c1bae2b`)하여 루프 원인 1개 제거. 남은 `incident_ledger.jsonl` 루프만 Step 2의 대상.

## 의제 (Claude 제안)

`evidence_gate.sh` 124-128 라인의 `tasks_handoff.req` deny 로직에 **전치 조건** 추가:

> `git diff --cached --name-only` 결과가 **제외 대상 로그 화이트리스트**에만 해당하면 deny를 스킵한다.

**화이트리스트 초안**: `.claude/incident_ledger.jsonl` 단일 항목 (세션 자동 증분 유일 항목)

## 근거

- 세션85 incident_audit 상위 5종 #5 패턴 65건 중 다수가 로그 단독 커밋에서 발생
- "행위 규정 위반(TASKS/HANDOFF 미갱신)"이 아닌 "훅 설계 결함" — 로그만 바뀐 커밋은 원래 TASKS/HANDOFF 갱신이 불필요
- 세션83 self-throttle 확장(GRACE 120s, tail -100)은 **로그 중복 기록을 억제**하지만 **루프 자체는 해결 못 함**

## 예상 반대 논리

- **(a) 일관성 원칙**: TASKS/HANDOFF 갱신 의무는 모든 커밋에 적용해야 감시 일관성 유지 — 예외 두면 구멍
- **(b) 정책 방향**: 자동 로그 커밋은 `/finish` 스킬로 세션 종료 시 묶어 처리하는 것이 정책적으로 올바름. 훅 변경보다 운영 습관 변경이 먼저
- **(c) 화이트리스트 리스크**: 한번 열면 다른 로그 파일도 연쇄 추가 요청이 들어와 확대될 위험

## 판정 요청

- **채택**: 화이트리스트 전치 조건 추가 → 세션87+ 구현 이월
- **보류**: 반대 논리 근거 수집 → 차기 세션 재논의
- **버림**: (a) `/finish` 강제 + (b) self-throttle 추가 튜닝 2안 이월

## B/A 분류 판정

- 변경 대상: `.claude/hooks/evidence_gate.sh` — 실행 흐름·판정 분기 변경 → **B 분류**
- 자동 승격 트리거 해당 → 사용자 "2자 토론" 명시 지시이나 B 분류는 원칙적으로 3자 승격 대상
- **처리**: 2자 토론은 본 의제에 대한 찬반 논리 정제용. 채택 시 실제 구현 전 3자 토론 승격 필요(세션87+)

## 본 토론의 범위

- 본 토론은 **"예외 규칙 도입 자체의 찬반"**에 한정
- 실제 `evidence_gate.sh` 코드 변경은 채택 시에도 본 세션 내 금지 → 3자 토론 이월
