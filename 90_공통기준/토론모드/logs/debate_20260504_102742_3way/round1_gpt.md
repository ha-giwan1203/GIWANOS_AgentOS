# Round 1 — GPT 본론

수령 시간: 2026-05-04 10:34 KST
모델: gpt-5-5-thinking
응답 길이: 7144자

## 핵심 결론
4중 적층 방향은 맞지만 실효 1순위는 메모리/CLAUDE.md가 아니라 Stop hook decision:block으로 "질문형 종료"를 막는 것.

## 우선순위 평가
1순위: Stop hook 질문형 종료 차단
2순위: UserPromptSubmit 추가 context
3순위: 사용자 발화 템플릿
4순위: 도메인별 durable authorization 문서
5순위: 메모리 추가

## hook 가능성 (Anthropic 공식 사양 인용)
- Stop hook: last_assistant_message 입력, decision:"block" 반환 시 Claude 멈추지 못함, stop_hook_active로 무한 루프 방지 필수
- UserPromptSubmit: 사용자 prompt 처리 전 실행, additionalContext 주입, decision:"block"이면 prompt 차단·context에서 삭제 (위험)

## 5번째 layer 제안 — Task Authorization Receipt
- 위치: `.claude/state/task_authorization/current.json`
- 사용자 발화를 구조화한 작업 단위 권한증
- memory보다 강함, completion_gate가 근거로 사용 가능
- subagent·permission 정교화는 "묻지 말고 판단" 문제 직접 해결 못함

## 분리 진단 (가짜 이분법)
- 시스템 프롬프트 보수성 = 절대 천장
- 학습된 행동 default = 천장 아래 보수 기우는 경향
- CLAUDE.md/메모리 = 약한 누름 신호
- hook/receipt/gate = 외부 제어
- 실험적 분리만 가능 (4가지 변형 비교)

## 합의안 (GPT 핵심)
**기존 completion_gate.sh에 delegation phrase measurement만 Phase 0 추가**

- 새 hook 추가 금지 (메타 부채)
- 새 메모리 추가 금지
- 즉시 block 금지 (과차단 지옥)
- 7일 측정 후 Phase 1 block 전환 (별도 사용자 승인)
- task_authorization JSON은 Phase 2로 보류
- UserPromptSubmit은 prompt 지울 위험 → 보류

## 즉시 적용 코드
```bash
DELEGATION_RE='(진행할까요|박을까요|진입할까요|선택해\s*주세요|어떻게\s*할까요|원하시면|확인\s*부탁|결정해\s*주세요|A.*B.*선택)'

# stop_hook_active 무한루프 방지
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then exit 0; fi

# Phase 0: 측정만
printf '{"ts":"%s","type":"delegation_phrase","matched":"%s","mode":"measure"}\n' \
  "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$MATCHED" \
  >> "$PROJECT_ROOT/.claude/logs/delegation_guard.jsonl"
```

## 채택/보류/버림 (GPT 자체 정리)
**채택**: completion_gate에 measurement, 7일 측정, Phase 1 사용자 승인 후 전환, task_authorization Phase 2 보류, 메모리 추가 금지
**보류**: UserPromptSubmit context injection, durable auth 확대, 새 hook, subagent
**버림**: 메모리 자체 판단 추가, CLAUDE.md 반복, 무조건 차단, 발화 템플릿 강요

## Claude 라벨링 (하네스 분석)

| 주장 | 라벨 | 채택/보류/버림 | 근거 |
|------|------|----------------|------|
| Stop hook이 1순위 | 실증됨 | 채택 | Anthropic 공식 hook 사양 인용 |
| UserPromptSubmit prompt 삭제 위험 | 실증됨 | 채택 (보류 권고 수용) | 공식 사양 명시 |
| Phase 0 measurement only | 실증됨 | 채택 | 즉시 block의 과차단 위험 회피 |
| 새 hook 추가 금지 | 실증됨 | 채택 | 본 저장소 hook_log.jsonl 누적 부담 실증 |
| Task Authorization Receipt | 일반론 | 보류 | Phase 2까지 검증 후 |
| 즉시 4중 적층 도입 (Claude 가설) | 과잉설계 | 버림 | GPT 진단 수용 — 측정 선행 필요 |

## claude_delta 영향
- Claude 가설 "4중 적층 즉시 도입" → GPT가 "Phase 분리 + 측정 선행 + 새 hook 금지"로 강하게 누름
- 종합안에서 `partial` 변경 예상 (적층 방향 유지 + 실행 페이즈 분리)
