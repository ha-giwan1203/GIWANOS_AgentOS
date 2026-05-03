# Verify Receipt Gate 설계 plan — 2026-05-03

> 작성 시점: 2026-05-03 (KST)
> 작성 모드: C (시스템 수정 plan-first)
> 짝 문서: `verify_gate_self_analysis_20260503.md`
> 승인 단계: plan 작성 완료 (코드/hook/SKILL.md 미수정). Phase 0 도입은 별도 승인 필요.
> **갱신 이력**:
> - 2026-05-03 v2 — 1차 3way 판정(GPT PASS / Gemini 부분PASS) 보완 4건 반영 (active_skill 개별 파일화 + session_start_restore Clean-up + completion_gate error_message 규격 + Phase 0 종료조건 관측 정상성 기준).
> - 2026-05-03 v3 — 2차 3way 판정(**GPT PASS / Gemini PASS — 양측 합의**) 추가제안 A 2건 반영: (a) Phase 1 사전조건에 "고위험 SKILL 동시 실행 금지" 1줄 추가 (b) cleanup 결과를 STATUS.md 운영 요약에도 기록.

## 1. Context

ERP/MES 비가역 작업에서 "API 응답 OK = PASS" 우회가 80%(4/5건) 발생했다. 기존 completion_gate는 내부 문서 신선도만 검사하므로 외부 시스템 반영 여부를 측정할 축이 부재. 새 hook 추가 없이 기존 completion_gate에 "verify receipt 존재·신선·PASS" 단일 진입점만 끼우면 차단력이 생긴다. 자세한 진단은 짝 문서 §2~§5 참조.

## 2. 변경 대상 (정확 경로)

### 2.1 수정

| 파일 | 변경 내용 | 규모 |
|---|---|---|
| `.claude/hooks/completion_gate.sh` | line 92 직전 1곳 삽입 (정상 PASS 직전, write_marker/git/sync 검사 통과 후) | ≈30줄 |
| `.claude/hooks/hook_common.sh` | read-only helper 4개 추가: `skill_required_pattern`, `find_override_receipt`, `validate_override`, `iso_to_epoch` | ≈40줄 |

### 2.2 신규 데이터

| 경로 | 타입 | 책임 |
|---|---|---|
| `.claude/state/active_skill.json` | 단일 파일 | SKILL이 진입 시 작성, 종료 시 삭제 |
| `.claude/state/verify_receipts/` | 디렉토리 | 정상 verify receipt 보관 |
| `.claude/state/verify_receipts/_override/` | 디렉토리 | 수동 우회 receipt 격리 |
| `.claude/state/verify_receipts_required.json` | 단일 매핑 | 사람이 손편집 |

### 2.3 SKILL 측 (Phase별)

| 스킬 | Phase | 변경 내용 |
|---|---|---|
| d0-production-plan | 1 | verify_run.py에 receipt 출력 stub 추가 + active_skill 작성/삭제 |
| jobsetup-auto | 2 | verify.py 신규 (read-after-write) + active_skill 작성/삭제 |
| production-result-upload | 2 | verify.py 신규 (list API 재조회) + active_skill 작성/삭제 |
| line-batch-management | 3 | verify.py 신규 + active_skill 작성/삭제 |
| assembly-cost-settlement | 3 | verify.py 신규 + active_skill 작성/삭제 |

### 2.4 금지 사항

- 새 hook 파일 추가 X
- 새 자연어 규칙/메모리 추가 X
- "다음부터 반드시 확인하라" 식 경고 추가 X
- async hook으로 PASS 차단 시도 X
- API 응답 OK만으로 receipt 인정 X

## 3. active_skill marker 표준 (v2 — 개별 파일 구조)

> **v1 → v2 변경**: 단일 `active_skill.json` 폐기. Gemini 보류 의견(sub-agent 다중 실행 race + Claude crash 시 단일 파일 잔류 위험) 채택. 디렉토리 + task_id별 개별 파일.

위치: `.claude/state/active_skills/{task_id}.json`
(디렉토리 신설. 다중 SKILL 동시 실행 안전.)

```json
{
  "task_id": "20260504_sp3m3_morning",
  "skill": "d0-production-plan",
  "started_at": "2026-05-03T11:30:12Z",
  "session_key": "session_2026-05-03_a0f15a18",
  "expected_receipt": ".claude/state/verify_receipts/d0-production-plan_20260504_sp3m3_morning.json"
}
```

### 3.1 책임 분리

- **생성**: SKILL 진입 시 SKILL 자신이 `active_skills/{task_id}.json` 작성 (SKILL.md Step 1에 receipt requirement 짧은 명시 포함)
- **삭제**: SKILL 종료 시 SKILL이 자신의 task_id 파일만 삭제 (PASS/FAIL 무관)
- **검사**: completion_gate가 `active_skills/` 디렉토리에서 가장 최근 mtime 파일 1개 확인 → 존재하면 `expected_receipt` 경로 검사. 디렉토리가 비어 있으면 receipt 검사 자체를 건너뜀
- **다중 SKILL**: 동시 실행 시 각자 자기 task_id 파일만 관리 → race 없음

### 3.2 stale marker 처리 + session_start_restore Clean-up (실패/중단/crash 대비)

**런타임 stale 판정** (completion_gate):
- `now - active_skill.started_at > 24h` → stale 판정 → receipt 검사 건너뛰고 `hook_log.jsonl`에 `active_skill_stale skill=$SKILL task=$TASK_ID age=Xh` 기록
- 24h 기준은 ERP 일일 작업 사이클. 짧은 SKILL(≤1h)은 Phase별 SKILL.md에서 별도 단축 가능 (별도 의제)

**세션 시작 시 자동 Clean-up** (Gemini 권고 채택):
- `session_start_restore.sh`가 매 세션 시작 시 `active_skills/` 디렉토리 스캔
- 24h 초과 파일은 `active_skills/_stale/{날짜}/` 하위로 이동 (삭제 X — 추적 보존)
- 이동 시 `hook_log.jsonl`에 `active_skill_cleanup count=N` 기록
- **STATUS.md 운영 요약에도 1줄 기록** (Gemini v3 A제안): `[YYYY-MM-DD] active_skill_cleanup: N건 _stale/로 이동` — 사용자가 세션 시작 시 즉시 인지 가능
- 효과: Claude 강제 종료 후 다음 세션이 잔류 marker로 Locked 되는 사고 방지
- 24h 미만 파일은 손대지 않음 (정상 작업 가능성)
- helper 함수 위치: `hook_common.sh`의 `cleanup_stale_active_skills()` 신설, `session_start_restore.sh`에서 호출 (STATUS.md 기록 포함)

**왜 1단계 + 2단계 둘 다 필요한가**:
- 세션 시작 cleanup만 두면 → 같은 세션 안에서 24h 넘긴 marker가 잔류
- 런타임 stale 판정만 두면 → 다음 세션에 marker가 영원히 남음
- 두 단계가 합쳐져야 "정상 동작 시 자동 정리 + 비정상 종료 시 다음 세션 자동 회복"이 보장됨

### 3.3 효과

- "이 작업이 진행 중"이라는 명시적 신호 → hook_log 추론 없음
- task_id가 receipt 파일명과 1:1 매칭 → 신선도 판정 단순화
- 다중 SKILL 동시 실행 시 마지막 진입 SKILL만 검사 (동시 진입은 SKILL 설계 책임 — 별도 의제)

## 4. verify receipt 표준

위치: `.claude/state/verify_receipts/{skill}_{YYYYMMDD}_{target}.json`

```json
{
  "task_id": "20260504_sp3m3_morning",
  "skill": "d0-production-plan",
  "verify_command": "python verify_run.py --line sp3m3 --shift morning",
  "result": "PASS",
  "checked_at": "2026-05-03T11:42:08Z",
  "target_files": ["10_생산계획/2026-05-04_SP3M3_조간.xlsx"],
  "external_system": {
    "name": "ERP",
    "endpoint": "GET /api/production/plan?date=20260504&line=sp3m3",
    "evidence_hash": "sha256:7b0a..."
  },
  "evidence": "ERP list API 재조회로 12행 모두 존재 확인",
  "source_script": "90_공통기준/스킬/d0-production-plan/verify_run.py",
  "session_key": "session_2026-05-03_a0f15a18"
}
```

### 4.1 판정 (active_skill.json 기준)

- `receipt.task_id == active_skill.task_id` 일치 필수
- `result != "PASS"` → block
- `checked_at < active_skill.started_at` → block (이전 receipt 재사용 방지)
- `external_system` 또는 `target_files` 중 하나 필수. **API 200 단독 금지**.

### 4.2 verify.py 책임

- 실제 ERP/MES/파일 read-after-write 검증 수행
- PASS일 때만 receipt 생성, FAIL이면 `result=FAIL` 기록
- API 응답 OK만으로 PASS 금지
- read-after-write 또는 list API 재조회 결과를 `evidence`에 명시

## 5. manual_override_receipt 표준 (수동 우회 규격화)

자유 텍스트 우회 폐기. 별도 receipt 타입으로 강제.

위치: `.claude/state/verify_receipts/_override/{skill}_{YYYYMMDD}_{target}.json`

```json
{
  "type": "manual_override_receipt",
  "task_id": "20260504_sp3m3_morning",
  "skill": "d0-production-plan",
  "approver": "하지완",
  "reason": "ERP 점검으로 verify API 일시 불가, 화면 확인으로 대체",
  "evidence_screenshot": "98_아카이브/override/20260503_d0_screen.png",
  "approved_at": "2026-05-03T11:50:00Z",
  "expires_at": "2026-05-03T23:59:59Z",
  "result": "PASS"
}
```

### 5.1 게이트 처리

- 정상 receipt 부재 시에만 `_override/` 검색
- `approver` 필수 (사용자명, 빈값 block)
- `reason` 필수 (≥10자, 빈값 block)
- `evidence_screenshot` 또는 `evidence` 필수 (둘 다 빈값이면 block)
- `expires_at` 필수, `now > expires_at`이면 block (최대 24h 강제 — 게이트 검사)
- 사용 시 `hook_log.jsonl`에 `override_used` 이벤트 기록 (감사 추적)

### 5.2 효과

- "수동 우회 가능"이라는 자유도 제거. 우회도 게이트가 검사
- approver/reason/expires_at 부재 시 우회 자체 차단
- 24h 만료로 영구 우회 방지

## 6. SKILL → receipt 매핑

위치: `.claude/state/verify_receipts_required.json` (단일 JSON, 수동 편집)

```json
{
  "version": 1,
  "default": "permissive",
  "skills": {
    "d0-production-plan":      { "required": true,  "min_evidence": ["external_system"] },
    "jobsetup-auto":           { "required": false, "min_evidence": ["external_system"] },
    "production-result-upload":{ "required": false, "min_evidence": ["external_system"] },
    "line-batch-management":   { "required": false, "min_evidence": ["external_system"] },
    "assembly-cost-settlement":{ "required": false, "min_evidence": ["external_system"] }
  }
}
```

매핑 누락 SKILL은 default permissive (receipt 미요구). 자동 등록 없음 — 임의 SKILL 차단 사고 방지.

## 7. completion_gate.sh 삽입 의사코드 (≤30줄, line 92 직전)

```bash
# --- verify_receipt gate (insert before pass log at line 92) ---
ACTIVE="$PROJECT_ROOT/.claude/state/active_skill.json"
REQUIRED_MAP="$PROJECT_ROOT/.claude/state/verify_receipts_required.json"
RECEIPT_DIR="$PROJECT_ROOT/.claude/state/verify_receipts"
if [ -s "$ACTIVE" ] && [ -s "$REQUIRED_MAP" ]; then
  SKILL=$(safe_json_get "skill" < "$ACTIVE")
  TASK_ID=$(safe_json_get "task_id" < "$ACTIVE")
  STARTED_AT=$(safe_json_get "started_at" < "$ACTIVE")
  EXPECTED=$(safe_json_get "expected_receipt" < "$ACTIVE")
  REQ=$(skill_required_pattern "$SKILL" "$REQUIRED_MAP")
  AGE_SEC=$(( $(date +%s) - $(iso_to_epoch "$STARTED_AT") ))
  if [ "$AGE_SEC" -gt 86400 ]; then
    log_event "active_skill_stale" "skill=$SKILL task=$TASK_ID age=${AGE_SEC}s"
    REQ=""   # stale marker는 receipt 검사 건너뜀
  fi
  if [ -n "$REQ" ]; then
    FAIL=""
    if [ ! -s "$PROJECT_ROOT/$EXPECTED" ]; then
      OVR=$(find_override_receipt "$RECEIPT_DIR/_override" "$SKILL" "$TASK_ID")
      if [ -z "$OVR" ] || ! validate_override "$OVR"; then
        FAIL="missing_receipt_and_no_valid_override"
      fi
    else
      R_TASK=$(safe_json_get "task_id" < "$PROJECT_ROOT/$EXPECTED")
      R_RES=$(safe_json_get "result" < "$PROJECT_ROOT/$EXPECTED")
      R_TS=$(safe_json_get "checked_at" < "$PROJECT_ROOT/$EXPECTED")
      [ "$R_TASK" != "$TASK_ID" ] && FAIL="task_id_mismatch"
      [ "$R_RES" != "PASS" ] && FAIL="${FAIL}|result_not_pass"
      [ "$(iso_to_epoch "$R_TS")" -lt "$(iso_to_epoch "$STARTED_AT")" ] && FAIL="${FAIL}|stale"
    fi
    if [ -n "$FAIL" ]; then
      # Gemini B 추가제안 채택: error_message에 필요한 receipt 규격 명시 (디버깅 가이드)
      REASON_TEXT="[COMPLETION GATE] verify_receipt skill=$SKILL task=$TASK_ID fail=$FAIL\\n"
      REASON_TEXT="${REASON_TEXT}required: $EXPECTED\\n"
      REASON_TEXT="${REASON_TEXT}schema: {task_id=$TASK_ID, skill=$SKILL, result=PASS, checked_at>=$STARTED_AT, external_system|target_files 중 하나 필수}\\n"
      REASON_TEXT="${REASON_TEXT}override: .claude/state/verify_receipts/_override/${SKILL}_*_${TASK_ID}.json (approver+reason>=10자+evidence+expires_at<=24h)"
      echo "{\"decision\":\"block\",\"reason\":\"${REASON_TEXT}\"}"
      hook_timing_end "completion_gate" "$_CMG_START" "block_receipt"
      exit 0
    fi
  fi
fi
```

helper(`hook_common.sh` 추가): `skill_required_pattern`, `find_override_receipt`, `validate_override`, `iso_to_epoch`, `cleanup_stale_active_skills` (5개, read-only + cleanup 1개).

## 8. 단계별 적용

| Phase | 범위 | 행동 변화 | 종료 조건 (GPT A제안 반영 — 관측 정상성 기준) |
|---|---|---|---|
| 0 | gate 코드 + 빈 매핑 + active_skills/ 디렉토리 + cleanup 함수 | 0 (no-op) | 7일 동안: false-block 0건 + active_skill_cleanup 이벤트 정상 기록 + active_skill_stale 잔류 0건 + completion_gate timing 평균값 변동 ≤10% |
| 1 | d0-production-plan: SKILL이 active_skills/{task_id}.json 작성/삭제 + verify_run.py가 receipt 출력 → required:true. **사전조건(GPT v3 A)**: Phase 1 진입 전 "고위험 SKILL(d0-production-plan / jobsetup-auto / production-result-upload / line-batch-management / assembly-cost-settlement) 동시 실행 금지" 운영 규칙 1줄을 .claude/state/active_skills/README.md에 명시 → 최신 mtime 1건 검사가 다중 고위험 SKILL을 놓치지 않도록 보장 | d0 receipt 강제 | 1주 통과율 ≥95%, override 사용 0건 |
| 2 | jobsetup-auto, production-result-upload (active_skill + verify.py 신규) | 두 스킬 receipt 강제 | 1주 통과율 ≥95% |
| 3 | line-batch-management, assembly-cost-settlement | 전체 5개 강제 | 안정화 |

**Phase 0 종료조건 보강 (GPT A제안 + Gemini 종합 의견)**: "false-block 0건"은 행동 변화 0인 시기엔 관측 거의 불가능 → 대신 "관측 정상성"으로 측정.
- active_skill_cleanup 이벤트가 매 세션 시작 시 정상 기록되는가
- 24h 초과 stale marker가 디렉토리에 잔류하지 않는가
- completion_gate에 신규 코드 30줄 삽입 후 timing이 안정적인가 (평균 변동 ≤10%)
- hook_log.jsonl에 receipt 관련 신규 에러 로그 0건인가

각 Phase 종료 조건 충족 후 다음 Phase 진행. 미충족 시 해당 Phase에서 stop, 원인 분석.

## 9. R1~R5 반증

- **R1 진짜 원인?**: 우회 4건 모두 "verify 안 함"이 아니라 "verify 결과를 게이트가 못 봄". hook_log/incident_ledger 교차 검증으로 receipt 부재 외 가설(자연어 미준수, hook_log 지연) 매칭 실패. → **receipt 부재가 직접 원인**.
- **R2 즉시 영향?**: 매핑 default permissive + Phase 0 빈 매핑이라 일반 문서 작업 영향 0. ERP 도메인은 Phase 1부터 점진. commit_gate/final_check는 본 plan에서 미수정.
- **R3 같은 패턴 호출처?**: PASS 보고 발생 SKILL을 hook_log SkillStart로 분류 시 5개 외 영향 SKILL 없음. 일반 문서·기획 SKILL은 receipt 미요구.
- **R4 incident 유사 사례?**: 과거 ERP 누락 incident가 incident_ledger에 산발 기록되었으나 게이트 차단으로 이어진 적 없음. 본 설계로 차단 경로 확보.
- **R5 실패 시 롤백?**: `verify_receipts_required.json`에서 `required:false` 1줄 토글로 즉시 무력화. 매핑 파일 삭제 시 게이트는 receipt 검사 건너뜀. 정상업무 막힘 시 **자유 텍스트 우회 금지** — `_override/` 규격 receipt(approver+reason+evidence+expires_at≤24h)만 허용. ERP 잔존 위험 감소량 80% (4/5건).

## 10. 검증 방법 (도입 후)

1. **Phase 0 직후**: `hook_log.jsonl`에서 reason="block_receipt" 0건 확인 (no-op)
2. **Phase 1 합성**: d0 SKILL → verify_run.py를 receipt 미생성 모드로 실행 → "완료 보고" 발화 → block 발생 + reason="d0-production-plan task=... fail=missing_receipt_and_no_valid_override" 확인
3. **정상**: receipt 정상 출력 → PASS 통과
4. **회귀**: 스킬 호출 없는 일반 문서 작업의 "완료 보고" → 모든 Phase에서 통과
5. **stale marker**: started_at을 인위적으로 25h 전으로 조작 → block 미발생, hook_log에 `active_skill_stale` 기록 확인
6. **override 정상**: receipt 부재 + 정상 _override receipt 존재 → 통과 + hook_log에 `override_used` 기록
7. **override 검증 실패**: expires_at 만료 / approver 빈값 / evidence 빈값 → block 발생
8. **7일치 hook_log 재집계**로 false-block / true-block 분리 분석

## 11. 별도 분리 의제 (B 의제 후보)

본 plan 범위에서 제외, 별도 의제로 처리:

- commit_gate / final_check 확장 (verify receipt 검사 commit 단계로 확장)
- SKILL별 stale 기준 단축 (≤1h SKILL용)
- ~~다중 SKILL 동시 실행 시 active_skill 큐 관리~~ → v2에서 개별 파일로 흡수
- ~~stale marker 자동 청소 스크립트~~ → v2에서 session_start_restore Clean-up으로 흡수

## 12. v2 갱신 사항 요약 (3way 양측 판정 반영)

| 보완 | 출처 | 변경 위치 | 비용 |
|---|---|---|---|
| active_skill 단일 → 개별 파일 | Gemini item 1 보류 | §3 (구조 변경), §3.1 (검사 로직) | 디렉토리 1개 추가 |
| session_start_restore Clean-up 추가 | Gemini 종합 의견 | §3.2 (cleanup_stale_active_skills 신설), §2.1 (helper 5개로 증가), session_start_restore.sh 1줄 호출 | 함수 1개 + 호출 1줄 |
| completion_gate error_message 규격 가이드 | Gemini 추가제안 B | §3.6 (REASON_TEXT 다단 포함) | 코드 5줄 추가 |
| Phase 0 종료조건 "관측 정상성" 측정 4지표 | GPT 추가제안 A | §8 표 + Phase 0 종료조건 보강 단락 | 측정 명령 4개 |

**미반영 (별도 의제 대기)**: 없음 — 양측 보완 권고 4건 모두 plan v2에 흡수.

## 13. v3 갱신 사항 요약 (2차 3way 양측 PASS 합의)

| 보완 | 출처 | 변경 위치 |
|---|---|---|
| Phase 1 사전조건 "고위험 SKILL 동시 실행 금지" | GPT v3 A제안 | §8 Phase 1 행 |
| cleanup 결과 STATUS.md 1줄 기록 | Gemini v3 A제안 | §3.2 Clean-up 단락 |

**최종 합의 상태**: GPT PASS / Gemini PASS / 양측 추가제안 모두 A분류 즉시 반영. 별도 의제 0건. Phase 0 코드 삽입 진입 가능.

## 12. 최종 판정

**기존 completion_gate 확장으로 가능**. 새 hook 불필요. 본 plan은 분석/설계 단계 — 코드 수정은 Phase 0부터 별도 승인 필요.
