# 토론 결과 — 저장소 병목 우선순위 (2자 토론, 2026-04-23)

## 합의안

지금 당장 실행할 우선순위 3개:

1. **incident_ledger.jsonl 실분포 확인** (선행)
   - 로컬 전용 파일. Git/Drive에서 안 보이지만 현재 세션에서 접근 가능.
   - 이 단계 없이는 "상위 원인군" 자체를 정할 수 없음.

2. **incident ≤ 100 달성까지 원인군 직접 소거**
   - rule 추가 금지. 기존 rule로 처리 가능한 것만 일괄 소거.
   - 목표: 138 → 100 (현재 대비 -27%)

3. **TASKS 감량 + `.claude/state/meta_freeze.md` 조건부 억제 기준 저장**
   - 완료 이력·장기 보류·세션 메모 덩어리 → 98_아카이브로 이동
   - meta_freeze.md 내용: `parse_helpers 전환 확대 금지 / auto_resolve 신규 rule 추가 금지 / 예외: 현업 blocker 복구 + 오작동 수정`
   - TASKS에는 링크 1줄만 (감량 역설 방지)

## 미합의 쟁점

없음 (Round 1 합의).

단, critic-reviewer WARN 2건:
- Claude 독립 축 미흡: 파서 통일 우선순위 관점이 합의안에서 사라짐
- "실증됨" 라벨을 미래 실행계획에 적용 — 라벨 오용

## 즉시 실행안 (GPT 조건부 통과 반영 — 보정 2건)

1. `incident_ledger.jsonl` 원본 직접 집계 → 상위 원인군 3개 확정
2. `/auto-fix` 수리 루프 (집계 결과 기반)
3. TASKS.md 감량 + `.claude/state/meta_freeze.md` 생성
   - TASKS.md에 `meta_freeze.md` 링크 1줄 필수 포함 (다음 세션에서 무시 방지)

## 판정
- GPT Round 1: 동의
- GPT 최종: 조건부 통과 (보정 2건 반영 후 통과)
  - 보정1: /auto-fix 전 ledger 직접 집계 선행
  - 보정2: TASKS에 meta_freeze 링크 1줄
- Claude: 채택 3건 / 보류 0건 (WARN 수용)
- critic-reviewer: WARN
