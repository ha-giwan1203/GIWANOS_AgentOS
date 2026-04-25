# 세션107 incident 잔존 분석 (L-5 후속)

작성: 2026-04-25 KST
근거: `.claude/incident_ledger.jsonl` 전수 분석 (전체 1428건)

## 진행 처리 결과

| 항목 | 처리 전 | 처리 후 |
|------|---------|---------|
| 미해결 incident | 163건 | **139건** |
| session_drift | 27건 | **0건** (전수 resolved) |

### 처리 액션
1. **STATUS.md 헤더 갱신** (세션105 → 세션107) → 신규 session_drift 발생 차단
2. **HANDOFF.md 헤더 갱신** (세션106 → 세션107) → final_check 정합 통과
3. **session_drift 27건 일괄 resolved** (`resolved_by: session107_status_handoff_sync`)
   - 백업: `.claude/incident_ledger.jsonl.bak_session107_pre_drift_resolve`

## 잔존 139건 hook/원인 분포

| hook | 건수 | 주요 분류 | 비고 |
|------|------|----------|------|
| auto_commit_state | 28 | completion_before_state_sync 28 | 상태 sync 전 commit 시도. STATUS/HANDOFF 매 세션 갱신으로 신규 차단 가능 |
| ? (필드 빈 항목) | 26 | UNCLASSIFIED 28 | ledger 기록 형식 자체가 깨진 항목. 별 의제 필요 |
| commit_gate | 24 | pre_commit_check 21 | 커밋 전 체크 실패. push 차단 누적과 동반 |
| navigate_gate | 16 | send_block 16 | 토론모드 진입 차단. CLAUDE.md 미읽기 marker 누락 |
| evidence_gate | 14 | evidence_missing 25 | evidence req 미충족 |
| skill_instruction_gate | 11 | doc_drift 5 + 기타 | 스킬 지시문 미읽기 |
| harness_gate | 7 | harness_missing 7 | 하네스 분석 누락 |
| date_scope_guard | 6 | scope_violation 6 | 날짜 범위 가드 위반 |

## 다음 액션 권고 (별 의제로 분리)

### 의제 A — auto_commit_state completion_before_state_sync 28건
- **근본 원인**: 사용자/Claude가 코드 변경 후 TASKS/HANDOFF/STATUS 갱신 전에 commit 시도
- **이번 세션 효과**: STATUS/HANDOFF 매 세션 갱신 정착 시 자연 감소 예상
- **즉시 조치**: 추가 자동 해소 가능 (commit 후 state sync 완료 시점 기준 24h 이상 경과 항목 일괄 resolved)

### 의제 B — UNCLASSIFIED 28건 (hook/type 빈 항목)
- **근본 원인**: incident_ledger.jsonl 기록 시 hook/type 필드 누락. record_incident.py 호출 누락 또는 필드 형식 오류 추정
- **즉시 조치**: 기록 시점·전후 hook_log.jsonl 대조로 원인 hook 추정 → 별 의제

### 의제 C — pre_commit_check 21건 (commit_gate)
- **근본 원인**: push 차단 누적 + commit_gate가 push 단독 검증 시 final_check 스킵 후 회귀
- **이번 세션 효과**: push 정책 결정 후 일괄 해소 가능

### 의제 D — send_block 16건 (navigate_gate)
- **근본 원인**: ChatGPT URL 진입 시 debate CLAUDE.md 미읽기 marker (`debate_claude_read.ok`) 누락
- **즉시 조치**: 매 세션 진입 시 토론모드 사용 전 CLAUDE.md 자동 읽기 hook 추가 검토 (별 의제)

## 별 의제로 미분리 사유
잔존 139건은 5종 hook이 90%를 차지하므로 hook별 근본 원인 분석이 필요. 단일 incident_repair.py auto-resolve로 일괄 처리는 안전하지 않음 (실 차단 사유 vs 우발적 trip 구분 필요).
