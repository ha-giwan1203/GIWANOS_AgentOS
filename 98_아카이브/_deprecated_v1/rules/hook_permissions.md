# hook vs permissions 역할 경계 + 훅 등급

> 루트 `CLAUDE.md`에서 분리 (debate_20260428_201108_3way 빼는 안 1 / 세션122).
> 배경: `.claude/settings.local.json` permissions.allow가 110개까지 누적되며 1회용 16건 + 완전 중복 2건이 섞여 들어온 문제를 근본 해결. 상세 로그: `90_공통기준/토론모드/logs/debate_20260418_190429_3way/`.

## 경계 원칙

- **permissions = 도구 호출 허용 on/off 게이트** — "이 Bash/Write/MCP 호출 자체를 허용할지"
- **hook = 호출 시점 맥락 검증 (조건부 게이트)** — "호출 시점의 지시문/상태/커밋 기준 등 맥락이 맞는지"
- **기능 직교**: 동일 보안 목적이라도 permissions와 hook 중 하나만 씀. 중복 금지
- **포괄 Bash 허용 vs dedicated tool**: 포괄 `Bash(cat:*)`·`Bash(grep:*)` 등은 fallback. **우선순위는 Read/Grep/Glob** 전용 도구

## 신규 추가 5단계 의사결정 트리

permissions나 hook을 추가할 때 위에서 아래로 순서대로 묻는다.

1. **전역 규칙인가 일회성 예외인가?** — 1회용(PID·URL·특정 경로 하드코딩)이면 **등록하지 않는다**. 포괄 패턴(`Bash(echo:*)` 등)이 이미 있으면 그걸 쓴다. 포괄이 없으면 포괄 등록을 고려한다.
2. **도구 호출 허용 문제인가?** — 호출 자체를 막거나 풀어주는 문제면 `permissions`.
3. **호출 시점 맥락 문제인가?** — 호출 조건(지시문 읽음·커밋 기준 갱신 등)에 따라 허가가 달라지면 `hook`.
4. **둘 다 필요한가?** — 허용은 permissions로, 조건은 hook으로 분리. 한 곳에 섞지 않는다.
5. **기록/만료 정책이 필요한가?** — 일시적 허용이면 `.claude/state/` 또는 `hook_log.jsonl`에 기록하고 만료 조건을 문서화.

## settings 계층 분리 가이드

- **팀 공용 정책** (전역 허용·전역 hook): `.claude/settings.json` 또는 기준 문서 (Git 커밋)
- **개인·세션성 예외**: `.claude/settings.local.json` (gitignore 또는 최소 범위)
- 재분류 인벤토리: `90_공통기준/토론모드/settings_inventory_20260419.md`

## 재발 방지 훅

- `.claude/hooks/permissions_sanity.sh` (advisory): 1회용 패턴·완전 중복 자동 탐지 → stderr 경고 + `hook_log.jsonl` 기록. 차단 없음. 60분 캐시.
- `completion_gate.sh` 소프트 블록 — 동일 1회용 패턴 3회 누적 탐지 시 사용자 명시적 확인 프롬프트. **하드페일 사용 안 함** (제조업 급한 세션 중단 리스크 회피)

## 훅 등급 3종 (2026-04-19 의제5 합의)

> 활성 훅이 맞물린 상태에서 특정 훅 exit 1 전파 정책이 제각각이던 문제를 표준화. hook_common.sh 공통 래퍼 + .claude/hooks/README.md 등급 분류 테이블 참조. 활성 수 집계: `bash .claude/hooks/list_active_hooks.sh --count`.

- **advisory (경고성)**: 실패해도 세션 계속. `exit 0` 강제. stderr 로그만. `|| true` 허용 명시. 예: `permissions_sanity.sh`, `auto_compile.sh`, `notify_slack.sh`
- **gate (차단성)**: 실패 시 상위 도구 호출 차단. `exit 2` + JSON `decision=deny` 병행(belt-and-suspenders). `|| true` 금지. 예: `block_dangerous.sh`, `commit_gate.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh`
- **measurement (계측)**: 실패 영향 없음. `exit 0` 강제. timing·통계만 기록. `trap ERR` 무시. 예: timing 래퍼, `hook_log`

## 공통 래퍼 함수 (hook_common.sh 정의)

- `hook_advisory <hook_path>` — 실패 시 stderr 로그 + exit 0
- `hook_gate <hook_path>` — 실패 시 exit 2 전파
- `hook_measure <hook_path>` — trap ERR 예외 무시, timing만

## Phase 2-B 적용 현황 (2026-04-19 세션72)

- **exit 2 + timing 배선 완료 (6개 gate)**: `commit_gate.sh`, `block_dangerous.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh`
- **timing만 배선 (Phase 2 승격 보류)**: `debate_verify.sh` — `incident_ledger` `debate_verify` 태그 18건 잔존. incident 7일 0건 달성 시 Phase 2-C에서 exit 2 전환
- **completion_gate.sh 소프트 블록 추가**: 최근 7일 permissions 1회용 패턴 동일 라벨 3회 이상 누적 탐지 시 deny 1회(60초 쿨다운) — 하드페일 없음
- **나머지 훅 등급 분류**: `.claude/hooks/README.md` 표 참조. 일괄 timing 배선은 Phase 2-C 이월
