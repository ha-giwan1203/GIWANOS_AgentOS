# Phase 8 Baseline (pre-Phase7)

> 3way Round 1 (debate_20260503_152741_3way) 합의에 따라 본 baseline 기록.
> 공식 7일 측정은 Phase 7 완료 후 active worktree 3개 확정 시점부터 시작.
> 본 baseline은 Phase 5+6 완료 직후, Phase 7 prune 이전 상태의 정량 측정값.

## 메타데이터

| 항목 | 값 |
|------|-----|
| 기준 SHA | a26ebd8a |
| 직전 변경 | [C+Phase6] Permissions 130→15 union 정확 달성 |
| 측정 시각 | 2026-05-03 일요일 15:42 KST |
| 세션 | 138 |
| stable-before-reset 태그 | 7abf1b3f |

## Round 1 8개 목표선 측정값

| 목표 | Baseline (세션137 진입 시점) | Phase 5+6 후 | 목표 | 달성 |
|------|--------------------------|------------|------|------|
| rules count | 5개 | 1개 | 1 | ✅ |
| rules lines | 300줄 | 82줄 (essentials.md) | 100 | ✅ |
| Hook count | 36 | 5 | 5 | ✅ |
| Slash count | 33 | 7 | 5 | ⚠ 7 (2 초과 — 토론 인프라 4개 + 사용자 명령 3개) |
| Skill avg lines | 305 | 49 | 80 | ✅ (초과 달성) |
| Skill total lines | 6414 | 1024 (-84%) | 1680 | ✅ |
| Subagent count | 9 | 5 | 5 | ✅ |
| Permissions union | 130 | 15 (global 11 + local 4) | 15 | ✅ 정확 |
| Worktree count | 17~20 | 17 (미축소) | 3 | ⏳ Phase 7 |
| Always-loaded 토큰 | ~9394 | ~? (재측정 필요) | <1000 | ⏳ Phase 8 |

**달성률 6/8 = 75%**. Phase 7 + always-loaded 재측정 후 Phase 8 공식 7일 측정 진입.

## 부수 측정값 (공식 7일 측정 비교용)

| 항목 | 값 |
|------|-----|
| TASKS.md 줄 수 | 510 (token_threshold WARN 400줄 초과 110) |
| HANDOFF.md 줄 수 | 79 |
| MEMORY.md 인덱스 줄 수 | 28 |
| incident_ledger.jsonl 라인 수 | 1381 |
| MANUAL.md count | 19 (Phase 5 신설) |
| GLOSSARY.json terms | 69 |

## 공식 7일 측정 시작 조건

다음 모두 충족 시 Phase 8 공식 7일 카운트 시작:
1. ✅ Phase 7 완료 — active worktree 3개 확정 + 14개 archive/prune
2. ✅ baseline_post_phase7.md 신설 — Phase 7 후 측정값 박음
3. ✅ always-loaded 토큰 재측정 (목표 <1000)
4. ✅ TASKS/HANDOFF/STATUS 정합 (세션139 진입 시점)

## 4지표 측정 명령 (Phase 8 진입 시 사용)

### 지표1. always-loaded 토큰
```bash
# 루트 CLAUDE.md + @import rules/* 합산 추정
wc -c CLAUDE.md .claude/rules/essentials.md | tail -1
# 토크나이저 정확 측정은 별도 (현재 라인수·바이트 기반 근사)
```

### 지표2. 사용자 판단 생략 횟수
```bash
# 7일간 incident_ledger.jsonl에서 "user_decision_required" 또는 "결정 위임" 패턴 grep
grep -c "user_decision\|결정 위임\|어떤 옵션" .claude/incident_ledger.jsonl
```

### 지표3. 지침 문서 삭제량
```bash
# 7일간 deprecated 이동 라인 수
git log --since="7 days ago" --diff-filter=D --name-only | wc -l
git log --since="7 days ago" --pretty=format: --shortstat | grep deletions
```

### 지표4. 분노 사이클 (같은 지적 반복 빈도)
```bash
# 7일간 incident_ledger.jsonl에서 동일 source_file + failure_signature 패턴 반복 빈도
python3 .claude/hooks/incident_repair.py --json --limit 100 | jq '.[] | .source_file' | sort | uniq -c | sort -rn | head -10
```

## 예상 Phase 8 결과 (가설)

Round 1 합의 시 예측한 효과:
- 사용자 판단 생략 횟수 ↓ (5조건 외 묻기 금지 + 자체 판단 형식 강제 효과)
- 지침 문서 삭제량 ↑ (Phase 2~6에서 6042줄 감소 누적, 7일 운영에서 추가 삭제 예상)
- 분노 사이클 ↓ (행동 교정 메시지 0 + 출력의 건조함 원칙 효과)
- always-loaded 토큰 ↓ <1000 (rules essentials 82줄 + CLAUDE.md 81줄 + import 최소)

## 30일 평가 기준 (Round 1 합의)

> "30일 후 4지표 50% 이상 개선 없으면 stable-before-reset 복원"

baseline 측정값 대비 50% 개선 기준:
- 사용자 판단 생략 50%↓ — 측정 어려움 (정성 → 정량 변환 필요)
- 지침 문서 삭제량 7일간 1000줄+ 삭제
- 분노 사이클 50%↓ — incident 동일 패턴 반복 50% 이하
- always-loaded 토큰 <1000 (목표 달성률 100%)

## 합의 원본 참조

- Round 1 합의 (debate_20260503_101125_3way): `90_공통기준/토론모드/logs/debate_20260503_101125_3way/round2_consensus.md`
- 본 종결 합의 (debate_20260503_152741_3way): `round1_claude_synthesis.md` + `round1_cross_verify.md`
- 양측 본론: `round1_gpt.md` + `round1_gemini.md`

## 다음 세션 첫 행동 (HANDOFF.md 등록)

1. git worktree list — 17개 inventory
2. 각 worktree git status --short + git log -1 --oneline + 최근 수정 파일
3. Claude 분류 후보 표 작성
4. 사용자 active 3개 선택
5. 14개 archive (98_아카이브/_deprecated_v1/worktrees/) 또는 git worktree prune
6. git worktree list 재검증
7. baseline_post_phase7.md 측정 → Phase 8 공식 7일 카운트 시작
