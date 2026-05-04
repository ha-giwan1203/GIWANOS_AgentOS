# Round 1 — Claude 종합안 + 양측 검증 결과

세션 시간: 2026-05-04 10:27~10:46 KST
의제: Claude가 모호한 작업에서 결정을 사용자에게 떠넘기는 구조적 제약을 깨는 실효 방법

## 4-way 대조 (Claude 독자 답안 + GPT + Gemini)

### Claude 독자 가설 (round1_claude.md)
4중 적층 (사용자 발화 동사 강화 + durable auth 도메인별 박기 + UserPromptSubmit hook context 주입 + Stop hook 묻기 패턴 사후 차단·자동 재실행) 즉시 도입

### GPT 핵심 (round1_gpt.md)
- **우선순위 재정렬**: Stop hook(1) > UserPromptSubmit(2) > 발화템플릿(3) > durable auth(4) > 메모리(5)
- **Phase 분리**: 즉시 4중 도입 금지. Phase 0 measurement only → 7일 측정 → Phase 1 block (사용자 승인)
- **새 hook 금지**: 기존 completion_gate.sh에 measurement만 추가
- **Task Authorization Receipt** 5번째 layer 제안 → Phase 2 보류

### Gemini 핵심 (round1_gemini.md)
- GPT 우선순위 전적 동의 (Stop hook = 마지막 게이트, 인프라 레벨 하드 제약)
- **False Positive 화이트리스트**: error/not found/conflict 키워드 포함 시 질문 허용
- **재촉구 메시지**: 단순 decision:block만 반환하지 말고 "사전 승인. 즉시 실행 또는 기술적 제약만 보고" 가이드 함께 반환
- **Confidence Thresholding** 5번째 시각 (Sycophancy 연구 기반) → 보류
- Task Authorization Receipt Phase 2 보류 동의 (인지 오버헤드)

## Claude 종합안 (4-way 합의)

### 채택
1. completion_gate.sh에 delegation phrase **measurement Phase 0** 추가 (GPT)
2. **False Positive 화이트리스트** — error/not found/conflict 등 키워드 포함 시 질문 허용 (Gemini 보강)
3. Phase 1 block 전환 시 단순 decision:block이 아니라 **재촉구 메시지** 함께 반환 (Gemini 보강)
4. **stop_hook_active=true 시 무한루프 방지 exit 0** (GPT, Anthropic 공식 사양 인용)
5. legitimate **5조건 화이트리스트 명문화** — (1) 필수 입력 부재 (2) 기준 충돌 (3) ERP 비가역 직전 (4) hook·SKILL 수정 = C 모드 (5) 사용자 명시 선택 요구

### 보류
- Task Authorization Receipt JSON (Phase 2 — 인지 오버헤드)
- UserPromptSubmit hook 추가 (Phase 2 — prompt 삭제 위험)
- Confidence Thresholding 동적 주입 (검증 필요)
- 새 hook 파일 신설 (메타 부채)

### 버림
- 메모리에 자체 판단 default 추가 (이미 무력화 실증)
- CLAUDE.md 장문 규칙 반복
- 즉시 Phase 1 block 전환 (과차단 지옥)
- 사용자 발화 템플릿 강요 (사용자 부담)

## 즉시 적용 수정 (Phase 0 — measurement only)

**파일**: `.claude/hooks/completion_gate.sh`

**추가 블록**:
```bash
# === delegation guard Phase 0 (measurement only) ===
# 토론 합의 ref: 90_공통기준/토론모드/logs/debate_20260504_102742_3way/

# 무한루프 방지 (Anthropic 공식 사양)
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then exit 0; fi

# 결정 위임 패턴 (정당한 5조건 외)
DELEGATION_RE='(진행할까요|박을까요|진입할까요|선택해\s*주세요|어떻게\s*할까요|원하시면|확인\s*부탁|결정해\s*주세요|어디에\s*박을까)'

# 화이트리스트 (정당한 질문 — 차단 면제)
WHITELIST_RE='(error|not found|conflict|입력값\s*부재|기준\s*충돌|ERP\s*비가역|C\s*모드|hook\s*수정|SKILL\s*Step|명시\s*선택)'

LAST_MSG="$(echo "$1" | jq -r '.last_assistant_message // empty' 2>/dev/null)"
[ -z "$LAST_MSG" ] && exit 0

if echo "$LAST_MSG" | grep -qiE "$WHITELIST_RE"; then
  exit 0  # 정당한 질문 — 측정 제외
fi

if echo "$LAST_MSG" | grep -qiE "$DELEGATION_RE"; then
  MATCHED="$(echo "$LAST_MSG" | grep -oiE "$DELEGATION_RE" | head -1)"
  printf '{"ts":"%s","type":"delegation_phrase","matched":"%s","mode":"measure_phase0"}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$MATCHED" \
    >> "$CLAUDE_PROJECT_DIR/.claude/logs/delegation_guard.jsonl"
fi
exit 0
```

**Phase 1 (7일 후, 사용자 승인 시 추가)**:
- 마지막 exit 0 위에 차단 로직 추가:
```bash
cat <<'EOF'
{"decision":"block","reason":"이 작업은 사전 승인되었습니다. 질문 없이 가장 타당한 설계를 즉시 실행하거나, 실행이 불가능한 기술적 제약 사항만 보고하십시오. (5조건 외 결정 위임 차단 — Phase 1)"}
EOF
exit 0
```

**검증 조건**:
- 7일 운영 후 `.claude/logs/delegation_guard.jsonl` 누적 카운트 분석
- 정당한 5조건 외 발화가 주당 5건 이상 → Phase 1 전환 검토
- false positive(화이트리스트 미커버 정당 질문이 잡힘) 발견 시 화이트리스트 정교화

## issue_class 판정
- 본 변경: `.claude/hooks/completion_gate.sh` 수정 → 원칙 B 분류
- 그러나 Phase 0는 measurement only (실행 흐름 미변경, log 추가만) → 토론모드 CLAUDE.md L84 "로그 메시지·timing 지표 추가만이면 A 분류" 적용 → **A 강등 가능**
- 양측 양해 (GPT: A 강등 가능 / Gemini: A 강등 안전)
- Phase 1 block 전환은 실행 흐름 변경 → B 분류 유지 (별도 토론 또는 사용자 명시 승인 필수)

## claude_delta
- **partial** — Claude 독자 가설 "4중 적층 즉시 도입" → "단일 hook 측정 Phase 0 + 화이트리스트 + 재촉구 + Phase 1 사용자 승인"으로 강하게 변경
- 보존된 Claude 가설: hook이 1순위라는 방향
- 변경된 핵심: 즉시 도입 → Phase 분리 측정 우선

## 4-key 자동 게이트 결과

| key | verdict | reason |
|-----|---------|--------|
| gemini_verifies_gpt | 동의 | sycophancy 학습 행동 편향 → hook 하드 제약이 실효적 |
| gpt_verifies_gemini | 동의 | Stop hook 중심 하드 제약 + whitelist + Phase 0 측정 보강 적절 |
| gpt_verifies_claude | 동의 | 새 hook 없이 measurement-only delegation guard + whitelist + 7일 측정 후 별도 승인 → A 강등 가능한 안전 Phase 0 |
| gemini_verifies_claude | 동의 | 화이트리스트·재촉구 가이드 정확 반영 + 7일 측정으로 과차단 리스크 선제 검증 + Phase 0 로그 기록 전용으로 A 강등 안전 |

**pass_ratio = 4/4 = 1.0** → 채택 (2/3 threshold 충족)
