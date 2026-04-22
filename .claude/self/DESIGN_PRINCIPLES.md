# 자기유지형 시스템 설계 원칙 (DESIGN_PRINCIPLES)

> Plan glimmering-churning-reef Part 2 기반. 세션91 단계 VI-1 (2026-04-22) 신설.
> 사용자 "안전안" 선택 (자기학습 포기 + 자기유지 보장). 2자 토론 합의.
> 본 문서는 **CLAUDE.md / STATUS / HANDOFF 확산 금지** — 단일 원본.

## 원칙 1: Meta Depth = 0 (안전안)

- 자기학습 포기, 자기유지만 보장.
- 학습 루프 자동 hook 전부 제거. SessionStart는 정적 파일 출력만 허용.
- `.claude/self/summary.txt` 갱신도 **수동 실행**으로만 (주 1회 사람이 `selfcheck.sh` 실행).
- 이유: 자기학습 유지하면서 Whac-A-Mole 방지는 구조적으로 어려움. 야심안은 30일 안정화 후 재평가 여지로만 남김.

## 원칙 2: Observation-Gated Addition

- 새 메커니즘은 "막을 문제의 실측 데이터" 제시해야 도입.
- 제시 못 하면 hook 대신 memory 기록으로 시작.

## 원칙 3: Budget, not Count

- 4개 예산 지표 동시 관리:
  - **latency**: hook 총 PreToolUse ms
  - **false block**: 오차단율
  - **churn**: 상태 파일 쓰기 빈도
  - **prevented incident**: 실제 막은 사건 수
- CLAUDE.md · MEMORY.md · TASKS.md 라인 상한.
- 초과 시 기존 기능 제거 강제.

## 원칙 4: Sunset by Default (30일 TTL)

- 모든 새 기능 30일 TTL.
- 효용 증명 못 하면 자동 폐기.
- Plan glimmering-churning-reef 자체도 TTL 30일 적용 (2026-05-22 효과 평가).

## 원칙 5: 1 Problem ↔ 1 Hook (세션91 III 적용 완료)

- 코어 게이트 3종 범위 재정의:
  - **commit_gate**: Git/staging만
  - **evidence_gate**: 사전 근거만
  - **completion_gate**: 최종 완료 선언만
- Overlap 금지. 중첩 책임 분리.
- 회귀 트립와이어: `.claude/hooks/gate_boundary_check.sh` (smoke_fast 편입).

## 원칙 6: No Dormant Surface

- 훅 파일은 settings 등록분만 디렉토리 유지.
- 비활성 훅 즉시 `.claude/hooks/archive/`.
- raw == active 강제.

## 원칙 7: Single Source of Truth (세션91 V 진행 중)

- README · STATUS · CLAUDE.md에 훅 숫자 · 목록을 **수동 서술 금지**.
- `.claude/hooks/list_active_hooks.sh`가 유일 원본 (settings.json 파싱).
- 드리프트 발생 구조적 제거.

---

## 폐기된 정책 (2026-04-21 → 2026-04-22 세션91 IV/V에서 제거)

- Self-X Layer 1 — Health Summary 의무 (`health_check.sh` · `health_summary_gate.sh`)
- Self-X Layer 2 — T1 Self-Recovery (`self_recovery_t1.sh`)
- Self-X Layer 4 — Circuit Breaker (`circuit_breaker_check.sh`)
- B5 Subtraction Quota (`quota_advisory.sh` + protected_assets.yaml quota/ttl 블록)

폐기 근거: `90_공통기준/토론모드/logs/debate_20260422_stage3_2way/SUMMARY.md`
원본 보존: `98_아카이브/session91_glimmering/protected_assets_quota_~session89.yaml`

---

## 수동 점검 도구

| 도구 | 용도 | 실행 |
|------|------|------|
| `selfcheck.sh` | 주 1회 묶음 점검 | `bash .claude/self/selfcheck.sh` |
| `list_active_hooks.sh` | 활성 hook 자동 집계 | `bash .claude/hooks/list_active_hooks.sh` |
| `smoke_fast.sh` | 11건 결정적 검사 (SessionStart 자동) | `bash .claude/hooks/smoke_fast.sh` |
| `final_check.sh` | --fast / --full / --fix 모드 | `bash .claude/hooks/final_check.sh --full` |
| `gate_boundary_check.sh` | 게이트 3종 경계 트립와이어 | `bash .claude/hooks/gate_boundary_check.sh` |

## 재도입 조건

Self-X 또는 Quota 계열 재도입 시:
- 막을 문제의 **실측 데이터** 필수 (원칙 2)
- 30일 효용 증명 (원칙 4)
- 기존 기능 제거와 세트 (원칙 3)
- 단일 원본 위반 금지 (원칙 7)
- 사용자 명시 승인 + 3자 토론 승격 필수
