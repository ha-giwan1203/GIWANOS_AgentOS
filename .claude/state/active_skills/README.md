# active_skills/

verify receipt gate 활성 SKILL 표식 디렉토리.

## 구조

- `{task_id}.json` — SKILL 진입 시 작성, 종료 시 삭제 (Phase 1+ 적용)
- `_stale/{YYYYMMDD}/` — session_start_restore가 24h 초과 marker를 이동시키는 보관소 (삭제 X)

## 운영 규칙

**Phase 1 사전조건 (GPT v3 A제안 채택, 2026-05-03)**:
고위험 SKILL 5종(d0-production-plan / jobsetup-auto / production-result-upload / line-batch-management / assembly-cost-settlement) **동시 실행 금지**.
이유: completion_gate가 `active_skills/` 디렉토리에서 가장 최근 mtime 1건만 검사하므로, 다중 고위험 SKILL이 동시 실행되면 마지막 진입한 SKILL의 receipt만 검사돼 다른 SKILL이 누락될 위험이 있다.

Phase 0(no-op) 단계에서는 디렉토리만 신설되고 매핑 JSON에서 모든 SKILL이 `required:false`라 검사가 건너뛰어진다.

## 짝 문서

- 표준: `90_공통기준/업무관리/verify_receipt_gate_plan_20260503.md`
- 분석: `90_공통기준/업무관리/verify_gate_self_analysis_20260503.md`
- 매핑: `.claude/state/verify_receipts_required.json`
