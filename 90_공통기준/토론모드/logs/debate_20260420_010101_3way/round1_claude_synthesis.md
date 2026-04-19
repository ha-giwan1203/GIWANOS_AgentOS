# Round 1 — Claude 종합 설계안

## 채택/버림 확정

- **지적 1 (push-only 충돌)**: 3/3 채택 → evidence_gate에 push-only 면제 분기 추가
- **지적 2-(2) partial proof deny**: 2/3 채택 → smoke_test 부분 일치 deny 케이스 1건 추가
- **지적 2-(3) stale skill marker**: 안전망 채택 → smoke_test 추가 1건 (정책 변경 없음, Gemini 지적 엣지 케이스 방어)
- **지적 3 (STATUS.md)**: 3/3 버림 (GPT 자기 철회 + Gemini·Claude 버림) → 건드리지 않음

## 구현 설계

### 1. `.claude/hooks/evidence_gate.sh` 수정 — push-only 면제

**현재 (세션78 f31b8f22)**:
```bash
if is_commit_or_push; then
  if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
    deny "commit/push 차단. 이번 세션에 TASKS.md/HANDOFF.md 갱신 흔적이 없습니다." "tasks_handoff"
  fi
fi
```
`is_commit_or_push`는 `git commit|git push` 둘 다 매칭 → push-only도 deny.

**변경안**:
```bash
# 세션78 Round 1 합의: git commit만 검증. push-only 면제 (세션76 push-only 스킵 최적화와 정합)
# git push는 이미 commit된 내용을 원격에 반영하는 행위 — 문서 갱신 증거는 commit 시점에 수호
if echo "$COMMAND" | grep -qiE 'git commit'; then
  if ! fresh_ok "tasks_updated" || ! fresh_ok "handoff_updated"; then
    deny "commit 차단. 이번 세션에 TASKS.md/HANDOFF.md 갱신 흔적이 없습니다." "tasks_handoff"
  fi
fi
```

### 2. `.claude/hooks/smoke_test.sh` 수정 — 44-10/11/12 신규 3건

- **44-10**: push-only pass
  - 시나리오: ok 마커 없음 + `git push origin main` 명령 → pass
  - 기대: `permissionDecision: "deny"` 없음
  
- **44-11**: partial proof deny
  - 시나리오: `tasks_updated.ok`만 존재, `handoff_updated.ok` 없음 + `git commit` → deny
  - 기대: deny (OR 조건, 하나라도 누락이면 차단)

- **44-12**: stale skill marker deny (Gemini 엣지 안전망)
  - 시나리오: `skill_read__stale.ok`를 START_FILE보다 past mtime으로 생성 + skill_read.req + 도메인 편집 → deny
  - 기대: deny (fresh_file이 stale 마커를 자동 필터링 증명)

### 3. 미변경 (확정)

- `risk_profile_prompt.sh`: 세션78 수정 그대로 유지 (트리거 축소 + tasks_handoff 조기 블록 삭제 유지)
- 기존 smoke 44-3/44-4/44-5/44-6/44-7/44-8/44-9: 변경 없음 (회귀 방지)
- STATUS.md: 갱신 안 함 (3자 합의 버림)

## 양측에 요청할 1줄 검증

위 설계안(evidence_gate push-only 면제 + smoke 44-10/11/12)에 대해:
- verdict: 동의 / 이의 / 검증 필요
- reason: 근거 1문장

특히 확인 포인트:
- `git commit`만 grep하면 체이닝(`git commit -am x && git push`)은 commit 부분이 잡혀 검증됨 — 의도된 동작인지
- 44-10은 ok 마커가 아예 없을 때도 push는 통과 — `has_any_req` early-exit 흐름과 충돌 없는지
- 44-12의 stale 마커 생성은 `touch -t` 등으로 START_FILE보다 이전 mtime을 재현 — 실제 환경에서도 mtime 기반 필터가 신뢰 가능한지
