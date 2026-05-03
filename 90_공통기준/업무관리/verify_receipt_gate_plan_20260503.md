# Verify Receipt Gate 설계 plan — 2026-05-03

> 작성 시점: 2026-05-03 (KST)
> 작성 모드: C (시스템 수정 plan-first)
> 짝 문서: `verify_gate_self_analysis_20260503.md`
> 승인 단계: plan 작성 완료 (코드/hook/SKILL.md 미수정). Phase 0 도입은 별도 승인 필요.

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

## 3. active_skill marker 표준

위치: `.claude/state/active_skill.json` (단일 파일, SKILL 진입 시 덮어쓰기, 종료 시 삭제)

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

- **생성**: SKILL 진입 시 SKILL 자신이 작성 (SKILL.md Step 1에 receipt requirement 짧은 명시 포함)
- **삭제**: SKILL 종료 시 SKILL이 삭제 (PASS/FAIL 무관)
- **검사**: completion_gate가 active_skill.json **존재 여부만** 확인 → 존재하면 `expected_receipt` 경로 검사. 부재하면 receipt 검사 자체를 건너뜀

### 3.2 stale marker 처리 (실패/중단/crash 대비)

- `now - active_skill.started_at > 24h` → stale 판정 → receipt 검사 건너뛰고 `hook_log.jsonl`에 `active_skill_stale skill=$SKILL task=$TASK_ID age=Xh` 기록
- stale marker는 게이트가 삭제하지 않음 (사용자 추적 가능하도록 보존, 별도 청소 스크립트나 수동 처리)
- 24h 기준은 ERP 일일 작업 사이클. 짧은 SKILL(≤1h)은 Phase별 SKILL.md에서 별도 단축 가능 (별도 의제)

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
      echo "{\"decision\":\"block\",\"reason\":\"[COMPLETION GATE] verify_receipt skill=$SKILL task=$TASK_ID fail=$FAIL\"}"
      hook_timing_end "completion_gate" "$_CMG_START" "block_receipt"
      exit 0
    fi
  fi
fi
```

helper(`hook_common.sh` 추가): `skill_required_pattern`, `find_override_receipt`, `validate_override`, `iso_to_epoch` (4개, read-only).

## 8. 단계별 적용

| Phase | 범위 | 행동 변화 | 종료 조건 |
|---|---|---|---|
| 0 | gate 코드 + 빈 매핑 + active_skill 스키마 도입 | 0 (no-op) | 7일 false-block 0건 |
| 1 | d0-production-plan: SKILL이 active_skill 작성/삭제 + verify_run.py가 receipt 출력 → required:true | d0 receipt 강제 | 1주 통과율 ≥95%, override 사용 0건 |
| 2 | jobsetup-auto, production-result-upload (active_skill + verify.py 신규) | 두 스킬 receipt 강제 | 1주 통과율 ≥95% |
| 3 | line-batch-management, assembly-cost-settlement | 전체 5개 강제 | 안정화 |

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
- 다중 SKILL 동시 실행 시 active_skill 큐 관리
- stale marker 자동 청소 스크립트
- SKILL별 stale 기준 단축 (≤1h SKILL용)

## 12. 최종 판정

**기존 completion_gate 확장으로 가능**. 새 hook 불필요. 본 plan은 분석/설계 단계 — 코드 수정은 Phase 0부터 별도 승인 필요.
