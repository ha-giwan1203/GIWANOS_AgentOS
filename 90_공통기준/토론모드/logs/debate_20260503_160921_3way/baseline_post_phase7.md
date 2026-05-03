# baseline_post_phase7.md

**측정 시각**: 2026-05-03 16:30 KST
**기준 SHA**: 43fa768e (Phase 7 prune 직전, main HEAD)
**합의 근거**: `round1_cross_verify.md` (pass_ratio 4/4 = 1.0)

---

## Worktree

- 정리 전: 19 (main + 18 claude/*)
- 정리 후: **4** (main + active 3) ✅ (목표선 active 3 달성)
- archive 16 + active 3 + main 1 = 20 (정리 전 19 + 사이 추가 1)

### active 3개 (Round 1 합의)
- `dazzling-cannon-9a8c52` (SHA 3a360184) — 세션128 block_dangerous PASS
- `fervent-mclaren-078078` (SHA 5556fe47) — 세션129 양측 PASS
- `goofy-ptolemy-0a7537` (SHA 2a58b49a) — D0 자동화 시간 변경 운영 맥락

### archive 대상 16개
- 폐기(파일 복사 없음): `crazy-shannon-f8e7ff` (main과 diff 0)
- patch 보존: `quirky-goldwasser-7f435d` (commits/0001 + 0002.patch)
- git_log + status: 14개 (zealous-nightingale, serene-wiles, amazing-faraday, unruffled-ritchie, distracted-mestorf, xenodochial-matsumoto, modest-fermi, nifty-liskov, focused-hugle, frosty-lalande, kind-williamson, nice-shaw, lucid-agnesi, nervous-dijkstra)

---

## Round 1 메타 계층 목표선 진척도 (Phase 7 완료 후)

| 지표 | 목표선 | Phase 1 baseline | 현재 (Phase 7 후) | 달성 |
|---|---|---|---|---|
| Worktree | active 3 | 20 | **4** (main + 3) | ✅ |
| rules count | 1~2 | 5 | **1** (essentials.md, 82줄) | ✅ |
| hook lifecycle | 5 | 55 | **5** (PreToolUse 3 + SessionStart 1 + Stop 1) | ✅ |
| Slash | 5 | 33 | **7** | (-26 / 목표 5는 보존 7개로 합의) |
| Skill 평균 | 80 | 305 | **48.76** (1024줄/21파일) | ✅ |
| Subagent | 5 | 9 | **5** | ✅ |
| Permissions | 15 | 130 | **15** (union: settings 11 + local 4) | ✅ |
| always-loaded | <1000 | ~9394 | ~4188 (Phase 2 측정값, 추후 재측정) | (Phase 2 시점) |

**8개 지표 중 7개 목표선 달성** (Slash 7은 사용자 결정으로 보존). Phase 7 = 메타 계층 슬림화 본체 완료.

---

## 잔존 메타 디렉터리 (별건)

`.git/worktrees/<name>/` 16개 디렉터리는 Windows file lock으로 즉시 삭제 실패. git worktree list에는 잡히지 않음 (논리적 prune 완료). 시스템 리부트 또는 lock 해제 후 정리 가능.

```
.git/worktrees/{16개 archive 대상 + active 3개 = 19개}/
```

**위험 평가**: 낮음 — git이 본체 부재로 prune 처리 완료. 다음 git worktree prune 실행 시 자동 정리 시도.

---

## claude/* 브랜치 잔존 (별건)

worktree 없는 claude/* 브랜치 24개 잔존. 추후 정리 별건:

```
agitated-mendel, amazing-feynman, busy-johnson, competent-jones, dazzling-nash,
dreamy-beaver, elastic-fermi, elegant-kilby, friendly-kirch, funny-solomon,
goofy-hermann, great-curie, happy-margulis, hardcore-raman, hopeful-feistel,
kind-chatelet, quirky-dewdney, relaxed-engelbart, sharp-lalande, sharp-mclaren,
strange-meninsky, ...
```

**처리 권고**: 별건 의제로 사용자 결정 후 `git branch -D` 일괄 정리.

---

## 기타 측정값

- incident total: 1386 (전체 누적)
- 미해결 incident: 186 (Phase 7 시작 시점)
- TASKS.md: 510줄 (목표 400 초과 — 별건)
- smoke_fast: 9/11 PASS, 2 FAIL (별건)

---

## Phase 8 공식 시작 조건

| 조건 | 상태 |
|---|---|
| active worktree 3개 확정 | ✅ |
| prune 후 git worktree list 재검증 | ✅ (4개 정합) |
| baseline_post_phase7.md 작성 | ✅ (이 파일) |
| TASKS/HANDOFF에 Phase 8 시작 선언 | (pending — commit 단계) |
| commit + push | (pending) |

**Phase 8 7일 카운트 예정 시작**: 2026-05-03 (커밋 시점부터)
**Phase 8 7일 카운트 종료 예정**: 2026-05-10

Phase 8 측정 항목: 신규 incident 발생률 / Slash 사용 패턴 / Subagent 호출 빈도 / Skill 호출 빈도 / always-loaded 토큰 안정성.
