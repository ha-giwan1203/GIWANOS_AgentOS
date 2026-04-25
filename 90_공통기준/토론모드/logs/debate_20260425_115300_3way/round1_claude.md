# Round 1 — Claude 독자안 (선행 작성)

세션: 107 (2026-04-25 KST)
의제: navigate_gate.sh를 protected_assets.yaml 보호 자산에 등록할지 (B 분류 자동 승격)
배경: GPT 시스템 정합성 검토 L-4 지적 (커밋 `e7a9afbb`, push 차단 상태)

## 독립 분석 (실물 근거)

### 1. 현재 상태 (실측)
- `90_공통기준/protected_assets.yaml` 등록된 게이트: debate_gate, debate_independent_gate, debate_send_gate_mark, debate_verify, commit_gate, evidence_gate, evidence_mark_read, stop_guard, completion_gate, evidence_stop_guard, auto_commit_state, block_dangerous, protect_files, date_scope_guard, gate_boundary_check, risk_profile_prompt
- **navigate_gate.sh 미등록**
- `.claude/hooks/navigate_gate.sh`: 64행, ChatGPT URL 진입 차단 게이트 (chrome-devtools-mcp `navigate_page` type="url" + `new_page` 매처)
- Q3 incident 분류: navigate_gate `send_block` 11건 (실측 시점 15건, 상위 4위)

### 2. 회귀 위험 분석 (핵심)
**`grep -rn "protected_assets\.yaml" .claude/hooks/`**: 보호 자산 yaml을 실제로 강제하는 hook은 **없음**. `protect_files.sh`는 deny_extensions/deny_path_patterns만 검사할 뿐, yaml 등록 여부와 무관.
- → **등록 자체로는 navigate_gate.sh 수정/삭제 절차에 자동 차단 발생 안 함**
- → 운영 방해 가능성: 거의 없음 (정책 선언 문서)
- → 실제 강제는 사람·Claude가 yaml을 참조해 manual/replace-only 정책 준수 여부 판단할 때 발동

### 3. 등록 일관성 기준 (현 yaml 분류)
| class | 의미 | 예시 |
|------|------|------|
| core | OS 구동 필수 | smoke_test, smoke_fast, hook_common, json_helper, debate_verify |
| guard | 보안·차단 | debate_gate, commit_gate, evidence_gate, protect_files, block_dangerous |
| recovery | 재난 대응 | (현 yaml에 명시 항목 없음) |

navigate_gate는 **외부 연동 진입 차단** = guard 적합.

removal_policy:
- never: 영구 보호 (commit_gate, evidence_gate, debate_verify, smoke_test 등)
- replace-only: 대체 hook 증명 시만 교체 (debate_gate, debate_independent_gate, evidence_mark_read 등)
- manual: 사용자 명시 승인

navigate_gate는 **debate_gate와 짝**. 토론모드 진입 게이트(debate_gate)와 ChatGPT URL 진입 게이트(navigate_gate)는 함께 작동 → 동일 등급 `replace-only` 권고.

### 4. Claude 독자안

```yaml
- path: .claude/hooks/navigate_gate.sh
  class: guard
  reason: ChatGPT URL 진입 게이트 (chrome-devtools-mcp navigate_page type=url + new_page 매처). 토론모드 CLAUDE.md 미읽기 시 진입 차단. debate_gate.sh와 짝 게이트
  removal_policy: replace-only
```

위치: `protected_assets.yaml` debate 계열 블록(line 66-85) **하단**, `debate_send_gate_mark` 다음 행에 추가.

### 5. 회귀 위험 등급
**낮음**.
- 자동 강제 hook 부재 → 정책 선언만 추가
- 정책상 변경 절차 강화 효과 (사람이 yaml 참조 시 replace-only 인지)
- 실제 navigate_gate.sh 수정/삭제 자체는 막히지 않음

### 6. 부수 효과 (긍정)
- send_block 15건 상위 원인 hook이 보호 레지스트리 등록 → 향후 무단 삭제·교체 위험 감소
- debate 계열 게이트 군집화 (debate_gate / debate_independent_gate / debate_send_gate_mark / **navigate_gate**)
- DESIGN_PRINCIPLES Single Source of Truth 일치 (navigate_gate 운영 정책 단일 원본화)

### 7. 부수 효과 (부정)
- 향후 **protected_assets 검증 hook 신설 시** navigate_gate.sh 수정에 사용자 승인 필요 → 정상 운영 절차에 마찰. 단 현재는 검증 hook 부재이므로 즉시 발생 안 함.
- yaml 1행 추가만으로 incident 송단(send_block 11~15건) 자체는 줄지 않음. **L-5 incident 분류 의제와 별개로 처리해야 함**.

## 결론
**찬성**. class: guard / removal_policy: replace-only로 등록.
회귀 위험 낮음 (정책 선언 문서, 자동 강제 hook 부재). debate_gate와 짝 게이트 군집화.

## 검증 요청 (양측)
1. **회귀 위험 평가 동의 여부**: protected_assets.yaml 등록만으로 navigate_gate.sh 수정이 자동 차단되지 않는다는 분석에 동의?
2. **등급 분류 적절성**: class=guard / removal_policy=replace-only 분류가 debate 계열 짝과 일치하는지?
3. **반대 사유**: 등록을 반대할 근거가 있다면? (불필요/과잉설계/순환 가드 등)
