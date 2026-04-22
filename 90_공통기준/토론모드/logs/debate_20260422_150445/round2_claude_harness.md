# Round 2 — Claude 하네스 분석 + 교차 검증

## 하네스 분해 (summary_counts: 채택 6 / 보류 1 / 버림 0)

### 채택
1. **마커 A/B/C 3분류 + A=evidence-core 3종** — 라벨: 실증됨
   교차 검증: `grep "tasks_read\|handoff_read\|status_read\|domain_read\|skill_read$"` on evidence_gate.sh → 0 hits. C분류 5종은 evidence_gate 미참조 확인. week2 삭제 후보 타당
2. **boundary 시나리오 6건 (축1/축2/축3 각 2건씩)** — 라벨: 실증됨. smoke_test 신규 runtime 케이스 경로 타당
3. **1주차 1→2→3→4 순서** — 라벨: 실증됨
4. **2주차 5번 선행 = 1주차 4번 완료 + 1주 관찰** — 라벨: 실증됨. Claude 의견 (가)(나)(다) 반영 확인
5. **롤백 조건 4건** — 라벨: 실증됨. 단계별 롤백 신호 명확
6. **Claude 의견 (라) 채택 + "순서는 evidence 먼저"** — 라벨: 실증됨. "노이즈 축소 후 contract 설계가 단순"

### 보류
7. **"C분류는 week2 삭제"에 `tasks_updated` / `handoff_updated` 처리 누락** — 라벨: 구현경로미정
   교차 검증: [evidence_gate.sh:136](.claude/hooks/evidence_gate.sh) `fresh_ok "tasks_updated" || fresh_ok "handoff_updated"` — commit 시 직접 fresh_ok 검사 중. GPT 4번 변경요지 "tasks_handoff commit 경로 제거, commit_gate/final_check + completion_gate로 이관"과 일치하지만 실행계획 문서에는 별도 항목으로 분리되지 않음.
   결론: 1주차 4번 작업 세부 체크리스트에 **"evidence_gate.sh:112-140 블록(tasks_handoff req/ok 검증) commit_gate 또는 completion_gate로 이관"**을 명시 필요.

### 버림
없음.

## Claude 독립 교차 검증 결과

### evidence_gate.sh 실제 참조 현황 (grep -n)
- line 112: `if [ "$req_name" = "map_scope" ]` — map_scope **직접 참조 중** (B 유지지만 week1 4번에서 evidence 축 제거 대상)
- line 116: `"tasks_handoff"` — req 라벨 참조
- line 136-137: `fresh_ok "tasks_updated" || fresh_ok "handoff_updated"` + deny — **commit 시 직접 차단 근거**. 이관 필요
- line 168-182: `fresh_req "skill_read" || fresh_req "identifier_ref"` + skill_read__* 순회 + deny — **skill_read 그룹 직접 deny 근거**
- line 191-199: `fresh_req "map_scope"` + deny — **map_scope 직접 deny 근거**

### week1 4번 이관 체크리스트 (Claude 추가)
4번 작업 세부:
a. `evidence_gate.sh:112-140` tasks_handoff/tasks_updated/handoff_updated 검증 블록 **제거** → commit_gate/completion_gate로 이관(이미 completion_gate가 write_marker/after_state_sync로 동일 책임)
b. `evidence_gate.sh:186-203` map_scope 블록 **제거 또는 분리**. map_scope는 "운영 훅·settings 수정 전 선언" 용도 → 필요 시 별도 hook 또는 commit_gate로
c. `evidence_gate.sh:165-184` skill_read 그룹 **skill_instruction_gate로 이관** (이미 skill_read__<skill>.ok는 skill_instruction_gate 전담, evidence_gate의 보조 면제 조건 제거)
d. `risk_profile_prompt.sh:80-87` (HAS_HOOK_FILE/HAS_SETTINGS/HAS_MIGRATION) map_scope req 발행 블록 → b와 세트 이관
e. `risk_profile_prompt.sh:61-64` skill_read/identifier_ref req 발행 블록 → c와 세트 (identifier_ref는 evidence-core 유지, skill_read만 이동)

## 다음 단계 제안
- 3라운드(실물 수정 대상 파일 + 변경 전/후 체크리스트)는 **GPT 제안이지만 Claude는 과설계 판단**. 현재까지 나온 계획으로 충분히 실물 수정 착수 가능
- **토론 종결 + 종합 실행계획 문서(plan.md) 작성 → 사용자 검토 요청**이 합리적
- critic-reviewer Step 4b는 선택 (토론이 단순 설계 토론이라 생략 가능)
