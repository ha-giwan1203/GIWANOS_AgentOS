---
name: auto-fix
version: v1.0
description: >
  smoke_test/e2e_test FAIL 또는 미해결 incident를 분석하고 수정 후보를 제안하는 반자동 수리 스킬.
  "auto-fix", "자동 수리", "FAIL 분석", "incident 수리" 등을 언급하면 이 스킬을 사용할 것.
---

# auto-fix 스킬 v1.0

> Phase 3-1 오토리서치 루프. 반자동 — 분석+제안만, 자동 수정 없음.

## 트리거

- "auto-fix", "/auto-fix"
- "FAIL 분석", "smoke 실패 원인"
- "incident 수리", "자동 수리"

## 실행 절차

### Step 1. FAIL 감지

smoke_test 또는 e2e_test를 실행하고 출력을 임시 파일에 저장:

```bash
bash .claude/hooks/smoke_test.sh > /tmp/smoke_output.txt 2>&1
bash .claude/hooks/e2e_test.sh > /tmp/e2e_output.txt 2>&1
```

### Step 2. FAIL 파싱

incident_repair.py의 `--parse-test-output` 옵션으로 FAIL 항목 추출:

```bash
python .claude/hooks/incident_repair.py --parse-test-output /tmp/smoke_output.txt
python .claude/hooks/incident_repair.py --parse-test-output /tmp/e2e_output.txt
```

### Step 3. 미해결 incident 확인

```bash
python .claude/hooks/incident_repair.py --json --limit 5
```

### Step 4. 분석 + 제안 출력

각 FAIL/incident에 대해:
1. 다음 행동 (inferred_next_action)
2. 패치 후보 파일 (patch_candidates)
3. 검증 단계 (verify_steps)

### Step 5. 사용자 확인 후 수정

- FAIL 분석 결과를 사용자에게 보고
- 사용자 승인 후 패치 후보 파일 수정
- 수정 후 Step 1로 돌아가 재검증

## 주의사항

- 자동 수정 금지 — 분석+제안만 수행
- 패치 후보는 제안이지 확정이 아님
- 동일 FAIL 2회 연속 시 사용자에게 수동 개입 요청
- incident_repair.py의 auto-resolve는 규칙 명확 케이스(scope_violation, dangerous_cmd)만 대상
