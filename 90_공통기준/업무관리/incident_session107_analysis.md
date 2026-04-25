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

## 별 의제로 미분리 사유 (1차 분석 시점)
잔존 139건은 5종 hook이 90%를 차지하므로 hook별 근본 원인 분석이 필요. 단일 incident_repair.py auto-resolve로 일괄 처리는 안전하지 않음 (실 차단 사유 vs 우발적 trip 구분 필요).

---

## 추가 처리 (세션107 후속, 2026-04-25 두 번째 — 사용자 지시)

### 의제 A~D 일괄 resolved (139 → 47건)

| 의제 | hook / classification | 처리 건수 | resolved_by | 근거 |
|------|----------------------|----------|-------------|------|
| A | auto_commit_state / completion_before_state_sync | 30 | session107_l5_a_root_cause_cleared | 본 세션 작업 중 final_check FAIL trip. 현재 ALL CLEAR 달성 |
| B | UNCLASSIFIED (hook/type/detail 빈 entry) | 32 | session107_l5_b_invalid_entry_format | 데이터 가치 없는 형식 깨짐 entry |
| C | commit_gate / pre_commit_check | 21 | session107_l5_c_root_cause_cleared | 동 A. push 차단 누적이 final_check 정상화로 해소 |
| D | navigate_gate / send_block | 17 | session107_l5_d_marker_present | ChatGPT 진입 marker 누락 trip. 세션 진입 후 marker 정상 |
| **합계** | — | **100** | — | — |

ledger 백업: `.claude/incident_ledger.jsonl.bak_session107_pre_l5_resolve`

### 잔존 47건 분포 (정당한 차단 기록 — 일괄 resolved 부적절, 개별 검토 필요)

| classification_reason | 건수 | hook |
|----------------------|------|------|
| evidence_missing | 26 | evidence_gate 14 / skill_instruction_gate 12 |
| harness_missing | 7 | harness_gate 7 |
| scope_violation | 6 | date_scope_guard 6 |
| doc_drift | 5 | (분포) |
| 기타 (true_positive / gpt_verdict / debate_verify_block) | 3 | — |
| 기타 hook | 6 | commit_gate 3 / token_threshold_check 2 / send_gate 1 / gpt-read 1 / ? 1 |

### 신규 발생 방지 — 별 의제 (이월)

**의제 B-2 — record_incident 호출 시 hook/type 필드 누락 점검**:
- 32건의 UNCLASSIFIED 발생 코드 경로 추적
- record_incident.py 또는 hook_common.sh hook_incident wrapper 호출 시 누락 위치 식별
- 강제 필드 검증 추가 (필드 누락 시 호출 자체 거부)

**의제 D-2 — 매 세션 첫 진입 시 debate marker 자동 생성**:
- session_start_restore.sh가 debate_claude_read.ok marker 무효화 → 첫 토론모드 사용 시 매번 navigate_gate trip 발생
- 토론모드 진입 자동 marker 생성 또는 trip 1회 후 silence 정책 검토

**의제 A/C — auto_commit_state / commit_gate 정합 유지**:
- 매 세션 STATUS/HANDOFF 갱신 정착으로 자연 감소
- 별 처리 불요
