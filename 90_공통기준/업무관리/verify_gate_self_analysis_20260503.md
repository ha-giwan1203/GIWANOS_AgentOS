# Verify Gate 자체분석 — 2026-05-03

> 작성 시점: 2026-05-03 (KST)
> 작성 모드: C (시스템 분석)
> 산출물 위치: `90_공통기준/업무관리/`
> 짝 문서: `verify_receipt_gate_plan_20260503.md`

## 0. 진단 결론 1줄

**버그 아님. 설계 누락(missing wiring).** 기존 hook/gate는 정상 동작 중이며, "verify 결과"라는 입력 채널 자체가 시스템에 존재하지 않는다. SKILL.md의 verify 명세는 자연어 참조일 뿐, hook이 실행을 강제하지 않는다 (Skills는 Claude가 autonomously decides to use 하는 참조 구조).

## 1. 분석 범위

- 기존 gate/hook: completion_gate, evidence_gate, commit_gate, final_check, mcp_send_gate
- 핵심 SKILL 5개: d0-production-plan / jobsetup-auto / production-result-upload / line-batch-management / assembly-cost-settlement
- 우회 발생 사례: 최근 30일 incident_ledger / hook_log / 세션 로그
- 외부 자료: Claude Code 공식 hook 문서, Aider/Cline/Codex 패턴

## 2. 현재 gate/hook 역할 분석 (실물 파일 기준)

### 2.1 completion_gate.sh v8 (Stop hook, measurement)

핵심 로직:
```bash
LAST_TEXT=$(last_assistant_text)
if ! is_completion_claim "$LAST_TEXT"; then exit 0; fi
if [ ! -f "$MARKER" ]; then exit 0; fi
AFTER_SYNC=$(safe_json_get "after_state_sync" < "$MARKER")
if [ "$AFTER_SYNC" = "true" ]; then exit 0; fi
# 미동기 시 TASKS/HANDOFF/STATUS mtime 비교
```

검사 대상:
- "완료 보고 / 최종 완료 / work complete / ALL CLEAR / GPT 판정: PASS" 정규식 (hook_common.sh L166-176)
- `.claude/state/write_marker.json`의 `after_state_sync` 플래그
- TASKS / HANDOFF / STATUS 메타파일 mtime

**SKILL별 verify 실행 여부 검사: 없음**
**verify receipt 개념: 부재**

### 2.2 commit_gate.sh (PreToolUse/Bash, gate)

핵심 로직:
```bash
if ! echo "$COMMAND" | grep -qE 'git (commit|push)'; then exit 0; fi
RESULT=$(bash "$HOOKS_DIR/final_check.sh" "$MODE")
if [ "$EXIT_CODE" -ne 0 ]; then
  echo "{\"hookSpecificOutput\":{\"permissionDecision\":\"deny\",...}}"
  exit 2
fi
```

- git commit/push 직전 final_check 호출
- 실패 시 hard block (exit 2 + permissionDecision:deny)
- final_check가 verify를 안 보므로 commit_gate도 verify를 못 봄

### 2.3 final_check.sh

검사 항목:
- write_marker의 `after_state_sync`
- TASKS / HANDOFF / STATUS 메타파일 갱신
- --full 모드에서만 smoke_fast 실행

**도메인 verify 결과 미참조. SKILL별 verify 자동 실행 없음.**

### 2.4 evidence_gate / mcp_send_gate

- evidence_gate: req/ok 메타파일 위주 (실제 verify command 결과 미참조)
- mcp_send_gate: MCP 호출 차단 정책 (verify와 무관)

### 2.5 .claude/state/ 현황

| 파일/디렉토리 | 존재 | 용도 |
|---|---|---|
| `verify_receipts/` | **X (없음)** | — |
| `write_marker.json` | O | 전역 sync 플래그 (SKILL별 receipt 아님) |
| `d0_verify_notify.jsonl` | O | D0 자동실행 상태 알림 (receipt 아님) |
| `hook_log.jsonl` | O | 훅 이벤트 기록 |
| `incident_ledger.jsonl` | O | incident 누적 |

**verify receipt 개념이 가장 가까운 메커니즘**: completion_gate v8의 `after_state_sync` 플래그. 단, SKILL별이 아니라 전역 플래그.

## 3. 5개 핵심 SKILL verify 명세 현황

| 스킬 | SKILL.md 경로 | verify 명령 명시 | MANUAL.md 분리 | verify 스크립트 실존 | receipt 출력 | 게이트 연결 |
|------|---|---|---|---|---|---|
| d0-production-plan | `90_공통기준/스킬/d0-production-plan/` | O (Phase 7) | O | O (verify_run.py) | O (state JSON) | △ (전환 中) |
| jobsetup-auto | `90_공통기준/스킬/jobsetup-auto/` | O (17항목) | O | X | △ (run_*.json) | X |
| production-result-upload | `90_공통기준/스킬/production-result-upload/` | O (qty합계) | O | X | X | X |
| line-batch-management | `90_공통기준/스킬/line-batch-management/` | O (3개 무작위) | O | X | X (JS 메모리만) | X |
| assembly-cost-settlement | `05_생산실적/조립비정산/` 계열 | O (step6 PASS) | O | X | △ (엑셀 시트) | X |

### 스킬별 1줄 평가

1. **d0-production-plan** (Grade B): Phase 7 사후검증 + verify_run.py + 3중 원인분류 + lock 원자성 + dedupe 자동 실행. **강제력 있음** (스케줄러 + 백오프 + ERP/MES 반영 후 검증).
2. **jobsetup-auto** (Grade B): 17/17 검사항목 + SmartMES 화면 수치 확인 명시 + state/run_*.json 결과 저장. **절차 명시이나 강제성 미흡**.
3. **production-result-upload** (Grade A): "BI행수 = MES행수 + qty합계 일치" 명시, 건수만으로 PASS 금지·read-after-write 강조. **명세는 우수하나 자동화 미연결, API 200 그대로 PASS 위험**.
4. **line-batch-management** (Grade A): 무작위 3개 직접 확인 + _queueSummary.err=0. **메모리 기반 검증**(JS 배열, 파일 저장 없음). ERP 저장 비가역 — 수동 재작업 필요.
5. **assembly-cost-settlement** (Grade B): 8단계 파이프라인 + step6 PASS + 엑셀 시트 검증. step 재실행 가능, 캐시 활용. **강제력 보통**.

### 강제력 있는 스킬: 1개 (d0-production-plan만)

나머지 4개는 절차 명시이나 외부 게이트/자동 재시도 미연결 → 권고 사항 수준.

## 4. 우회 발생 원인 가설 판정

| 가설 | 판정 | 근거 |
|------|------|------|
| SKILL.md verify 명세가 hook과 미연결 | **○ 주원인** | 5개 중 4개 미연결 |
| completion_gate가 상태문서 중심이라 도메인 verify 미참조 | **○ 주원인** | `after_state_sync`만 검사 |
| evidence_gate가 API 응답 OK를 evidence로 착각 | △ | evidence_gate는 req/ok 메타 위주 (직접 원인 아님) |
| PostToolUse/async 구조라 차단력 없음 | X | completion_gate는 Stop hook, decision:block로 hard block 가능 |
| exit code 2 / decision:block 미사용 | X | commit_gate는 이미 사용 중 |
| verify.py가 receipt JSON 미생성 | **○ 직접 원인** | 5개 중 1개만 부분 생성 |
| Claude가 SKILL.md 읽어도 강제 장치 없음 | **○ 구조적 원인** | Skills는 autonomous reference |

## 5. 우회 사례 분석 (최근 30일, 5건 표본)

| 날짜 | 도메인 | 세션 | 우회 형태 | 근본원인 요약 |
|------|--------|------|----------|---------|
| 2026-04-25 | jobsetup v0.3 | 세션132 | final_check 통과만 신뢰 | phase 5(검사 입력)까지만 verify, phase 6(저장 클릭) 미검증 |
| 2026-04-27 | D0 morning | 세션110 | API 응답만 신뢰 | OAuth redirect 누락, schtasks LastResult=1 검증 부재 |
| 2026-04-28 | D0 morning | 세션110 | API + Chrome 상태 누락 | Chrome 복원 알림이 무인 auto-run에서 무시 |
| 2026-04-29 | D0 verify | 세션124 | 선행 verify 단계 폴백 미구성 | Phase 0/1/2 강제 종료만 정의, Phase 3+ 대기 미감지 |
| 2026-05-01 | D0 + jobsetup | 세션131 | OAuth redirect 지연 + timeout | 60s timeout 회복 실패, 5일 중 4일 반복 |

**verify receipt 부재가 직접 원인인 비율**: 4/5건 (80%) — 모두 ERP/MES 비가역 도메인.

공통 패턴:
1. 자동화 선행 (OAuth/SmartMES 진입 판정)
2. verify_run.py 같은 사후 검증 스크립트 활성 이전에 문제 발견 지연
3. 최종 단계(저장/등록 확인)가 timeout 또는 상태 다중정의로 미스캘리브레이션

## 6. 외부 자료 요약

- **Claude Code 공식 hook**: PreToolUse / PostToolUse / Stop hook 존재. Stop hook은 `decision:block`으로 종료 차단 가능.
- **PreToolUse**: `permissionDecision:deny` 또는 `exit 2`로 tool 실행 차단 가능.
- **async hook**: decision/block 계열 제어에 부적합 → PASS 차단용으로 쓰면 안 됨.
- **Skills**: Claude가 autonomously decides to use 하는 참조 구조. 강제 장치 아님.
- **Aider 패턴**: `--test-cmd` / `--auto-test` — "AI가 테스트했다고 말함"이 아니라 test command exit code로 판정.
- **Cline/Codex 사례**: 자동 권한은 sandbox/권한 범위 제한과 묶어야 함. verify 우회는 자연어 지침이 아니라 외부 gate로 막아야 함.

## 7. 결론

1. 기존 시스템에 "verify receipt" 입력 채널이 부재. write_marker / decision:block / exit 2 / 정규식 PASS 감지는 모두 존재.
2. completion_gate가 내부 문서 신선도만 검사하므로 ERP/MES 외부 시스템 반영 여부를 측정할 축이 없음.
3. SKILL.md의 verify 명세는 강제력 없는 참조. hook이 실행을 강제하지 않음.
4. 우회 4건/5건이 "API OK = PASS" 패턴 — receipt 도입 효과 80%.
5. **새 hook 불필요**. 기존 completion_gate에 단일 진입점 1곳(≈30줄) 삽입으로 가능.

설계안은 짝 문서 `verify_receipt_gate_plan_20260503.md` 참조.
