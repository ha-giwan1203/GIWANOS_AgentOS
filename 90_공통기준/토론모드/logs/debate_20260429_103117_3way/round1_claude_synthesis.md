# Round 1 — Claude 종합안 (Step 6-5)

## 4-way 대조 (Claude 6-0 / GPT / Gemini / 양측 1줄 검증)

| 항목 | Claude 6-0 | GPT 6-1 | Gemini 6-3 | 합의 여부 |
|------|-----------|--------|-----------|----------|
| 비중 (hook 미구현) | 30% | 40% | 70%+ | **부분 합의** — "hook 미구현이 본질" 방향 일치, 정확한 % 미합의 |
| 비중 (drift) | 50% | 35% | (간과로 판정) | 미합의 — 실증 측정 미실시로 이월 |
| 외부 자료 | 불필요 | 환경미스매치/반대 (Anthropic 공식·LangGraph 인용 가치) | 환경미스매치/반대 (현재 이벤트 활용 시급) | **합의** — 추가 일반 조사는 불필요, 공식 hook 문서 + 이벤트 기반 설계는 가치 |
| 메모리 리팩터 우선 | (1차안 미포함) | 동의 (11건 → 1건) | 동의 (Event-Condition-Action 단일 명제) | **만장일치** |
| hook 강제 | 1차안: gate 전환 가능 | 보류 (메타순환, advisory만) | 동의 (advisory만) | **합의** — advisory only, 자동 호출 금지 |
| hook 옵션 | stop 차단 | stderr 경고 + 추가 맥락 주입 | stderr 경고 + 직전 컨텍스트 주입 | **합의** — stderr advisory |
| gate 전환 | 1주 후 가능 | 과잉 | 무한 루프·토큰 낭비 위험 | **합의** — gate 보류, advisory 유지 |

## 채택안 (Claude 종합)

### 1. 메모리 리팩터 (선행 작업, Phase A)
- **대상**: feedback_auto_update_on_completion / feedback_no_idle_report / feedback_post_completion_routine / feedback_no_approval_prompts / feedback_independent_gpt_review / feedback_auto_update_on_completion 외 누적 11건 추정
- **방법**: 1개 통합 메모리로 압축 — "WHEN git_push_success THEN check_share_routine" 단일 Event-Condition-Action 명제
- **위치**: `memory/feedback_post_push_share.md` (신규 1건) + 기존 11건 중 통합되는 것은 **삭제 대신 본문에 deprecated 표기 + 통합 메모리 링크**
- **MEMORY.md 인덱스 갱신**: 11건 항목 → 1건으로 축약
- **claude_delta**: 양측 합의로 1차안 보강

### 2. PostToolUse(git push) advisory hook 신설 (Phase B)
- **위치**: `.claude/hooks/share_after_push.sh`
- **트리거**: PostToolUse + Bash 매처에서 `git push` 또는 `git push origin` 패턴 detect
- **동작 (advisory only)**:
  ```
  if (commit message contains [3way] OR docs(state) OR feat OR fix OR refactor)
     AND (.claude/state/last_share_marker absent or stale > 5min):
       echo "[share_after_push] git push 완료 감지 — share-result 필요 여부 확인 (3way/시스템 변경이면 공유 루틴 실행)" >&2
       hook_log.jsonl 기록
  ```
- **`exit 0` 강제 (advisory 등급)** — 차단 안 함, stderr만
- **자동 호출 금지** — share-result skill 자동 trigger 금지(양측 합의: 무한 루프·토큰 낭비 위험)
- **상한**: ≤30줄, 단일 파일
- **hook 카운트**: 35 → 36 (advisory 등급은 운영 부담 작음)

### 3. 7일 운영 + ROI 검증 (Phase C)
- 1주(2026-04-29 ~ 2026-05-06) advisory 운영
- `hook_log.jsonl`에서 share_after_push 발화 횟수 + 그 후 share-result 실행 비율 측정
- **gate 전환은 반드시 보류** — 양측 합의(과잉)
- 1주 후 발화 후 미실행률 50% 이상이면 hook 효과 부족 → 다른 안 검토 (메모리 리팩터 추가 다듬기 등)

### 4. 비중 합의 (정량 미측정 인정)
- "hook 미구현이 본질이며 단일 가장 큰 비중(40~70%)"으로 합의
- attention drift 정확 비중은 미합의 — 클린 세션 vs 현행 비교 실증은 별도 의제로 이월 (debate_20260428 [잔존]에 동일 항목 명시됨)

## claude_delta: **partial**
- 1차안에서 메모리 리팩터 추가 흡수 (양측 합의)
- 1차안에서 gate 전환 가능성 → 보류로 변경 (양측 합의)
- 1차안에서 stop 차단 옵션 → stderr advisory로 통일 (양측 합의)
- 1차안 비중 30% → 40~70% 합의로 조정

## issue_class: **B**
- hook 신설 + 메모리 통합은 시스템 흐름·판정 변경
- skip_65 불가 (조건 B·C 미충족) — 6-5 수행 필수

## skip_65: **false**

## 양측 최종 검증 요청

본 종합안 원문 전체를 양측에 동봉하여 1줄 검증 요청 (동의 / 이의 / 검증 필요 + 근거 1문장).
