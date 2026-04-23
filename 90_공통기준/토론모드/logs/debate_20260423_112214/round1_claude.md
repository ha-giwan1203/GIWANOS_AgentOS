# Round 1 — Claude 독립 하네스 + 본 안건 제시

## 세션 메타
- 모드: 2way (Claude × GPT)
- 대화방: 클로드코드 시스템 분석 (기존 대화 이어서)
- 의제: `incident_repair.py` auto_resolve() 규칙 6 추가 — pre_commit_check 시간+조건 기반 해소
- 맥락 연결: GPT Turn 1 우선순위 ⑤ "ledger 증가 억제 수치화" 구체안

## GPT Turn 1~2 응답에 대한 독립 하네스 (채택/보류/버림)

### 채택 (실증됨)
| 항목 | 라벨 | 근거 |
|------|------|------|
| A1. 파싱 과잉 의존 | 실증됨 | 세션96 오늘 `_get_date`/`_get_session` sed 파싱 + git index 우선 순서 때문에 drift 미감지. working tree 우선으로 수정 (커밋 `7474e9ed`) |
| B1. gate 반환 일관성 부족 | 실증됨 | 세션72 Phase 2-B에서 6개만 exit 2 전환. evidence_gate/completion_gate는 exit 0 + deny JSON 잔존 |
| Pri 4. final_check 검증축 분리 | 실증됨 | 오늘 drift 감지 강화도 문서 정합 축에만 몰려 실행 안전과 엉킴 |

### 보류
| 항목 | 라벨 | 근거 |
|------|------|------|
| A3. incident_ledger Git 추적 분리 | 실증됨 + 과잉설계 | 방향성 맞지만 즉시 분리는 과잉. 감사 보존 vs diff 잡음 trade-off. 대안: ledger 내부 auto-resolve 강화(=본 안건) |
| C1. debate_verify advisory 상태 | 일반론 (맥락 미반영) | CLAUDE.md에 Phase 2-C 재평가 계획 명시. incident 18건 해소 시 exit 2 전환 예정. "완료 안 됨"이 아니라 "의도적 대기" |
| Pri 5. debate_verify/state_rebind 정리 | 보류 | 상위 C1과 동일 맥락 |

### 버림
| 항목 | 라벨 | 근거 |
|------|------|------|
| B2. selfcheck 깊이 제한 | 환경미스매치 | smoke_fast 11건은 **존재성 빠른 확인** 전용, smoke_test 211건이 깊이 검증. 역할 분리 설계. 세션93 211건 확장 실증. selfcheck 얕다는 판정은 smoke_test 계층 미반영 |

### 주관 점수 (8/7/5/4, "기능은 산다 사람이 관리해줘야")
- 검증 불가 영역 (일반론). 방향성 참조만.

## 요약
- 채택 3건 / 보류 3건 / 버림 1건
- 채택 3건 중 A1·Pri4는 오늘 세션96에서 이미 부분 구현 시작됨

## 본 안건 (GPT Pri 5 "ledger 증가 억제 수치화" 구체안)

### 현황
- 미해결 incident 375건 중 **202건(54%) = `classification_reason=pre_commit_check`**
- 전부 동일 패턴: `commit_gate → final_check --fast/--full FAIL → gate_reject`
- 최다 fingerprint 16건 반복 (`cd129792fc8e4770`), 시간범위 2026-04-14~04-22 (세션93 이전)
- 현재 `final_check` ALL CLEAR + `smoke_test` 211/211 PASS + `smoke_fast` 11/11 PASS

### 제안 — `incident_repair.py auto_resolve()` 규칙 6 추가
조건 (AND 모두 충족):
1. `classification_reason == "pre_commit_check"`
2. `ts < 현재 - 72h`
3. 현재 `bash .claude/hooks/final_check.sh --fast` exit 0
4. 현재 `bash .claude/hooks/smoke_fast.sh` exit 0

→ `resolved=true` + `resolved_by="auto_rule6"` + `resolved_reason="pre_commit_check_stale_after_final_check_pass"`

### 세션93 /auto-fix B-1 지적 반영
- 그때 "옵션 B + 72h" 제안 → GPT "원인-해소 연결 약함" 지적 받고 철회
- 이번 안은 그 지적에 답하는 구조:
  - **원인**: commit_gate가 final_check FAIL로 차단
  - **해소 증명**: 현재 final_check PASS + smoke PASS (명확한 "문제 없음" 증명)
  - **72h 버퍼**: 최근 발생건 보존 (아직 해결 중일 수 있음)

### 효과/리스크
- 202건 일괄 해소 → 미해결 375→173 (-54%)
- 세션93 /auto-fix -37%(571→362)에 이어 누적 ledger 잡음 대규모 해소
- 리스크: 실제 잔존 문제 기록 섞일 가능성 → 72h + final_check + smoke 3중 조건으로 완화

### 판정 요청
통과 / 조건부 통과 / 실패 중 하나로 한국어 응답.
