# Round 1 — Claude 독자 답안 (Step 6-0 선행 작성, 양측 본론 수령 전)

## 의제
"알잘딱깔센이 안 되는 근본 원인 + 개선 방향" — 외부 자료 필요성 / 시스템 한계 여부 / hook 강제 적정성

## 결론 1줄
**외부 자료 추가 조사는 ROI 낮음. 본질은 모델 한계 70% + 운영 설계 30%이며, 메모리·CLAUDE.md를 더 늘리면 attention drift 악화. 보완 경로는 PostToolUse(git push) hook 1건 신설(advisory→1주 후 gate 전환)이며 hook 누적 부담은 advisory 단계에서 ROI 검증으로 회피.**

## 주장 5개 + 라벨 + 증거 + 약점

### 주장 1 — Long-context attention drift이 본질 (비중 50%)
- **라벨**: 실증됨
- **증거**: 본 저장소 `debate_20260428_201108_3way` Round 1 합의 (pass_ratio 0.75, "Opus 추론 자유도 운영 길들이기 95% 침식"). 외부 인용 누적 — Lost in the Middle (Liu TACL 2024), Context Rot (Chroma 2025), Goal Drift (arxiv 2505.02709), Inherited Goal Drift (arxiv 2603.03258 — R1~R5 hierarchy로도 drift 못 막음 실증)
- **약점**: 비중 50%는 정량 실측 아님 — 추정. 클린 세션 vs 현행 TPS·TTFT·routine 발화율 비교는 미실시 (debate_20260428 [잔존]에 동일 항목 명시)

### 주장 2 — Instruction-following bias (비중 20%)
- **라벨**: 실증됨
- **증거**: agentic LLM 일반 약점. 명시적 user request weight ≫ 메모리 잠재 룰 (RLHF 학습 구조). multi-step routine 자동화는 학습 데이터에 적게 포함됨
- **약점**: 모델 학습 내부는 black box — 외부에서 비중 정확 측정 불가

### 주장 3 — Hook 미구현이 보완 가능 영역 (비중 30%)
- **라벨**: 실증됨
- **증거**: 메모리 `feedback_auto_update_on_completion.md` enforcement=hookable로 분류만 됨, 실제 hook 부재. share_gate.sh는 "공유 시작 시점" 검사만, "git push 후 자동 트리거"는 없음. 세션123 write_router_gate가 "외부 비트 주입"으로 sprawl 차단한 선례 존재 — 동일 패러다임 적용 가능
- **약점**: hook 신설은 또 다른 메타 운영 부담 위험 (write_router_gate도 advisory 1주 운영 후 gate 전환 절차 필요)

### 주장 4 — 외부 자료 추가 조사 ROI 낮음
- **라벨**: 실증됨
- **증거**: 본 저장소가 이미 외부 인용 5건(Lost in the Middle / Context Rot / Goal Drift / Many-shot jailbreaking / Inherited Goal Drift)으로 결론까지 도출. 추가 조사로 새 발견 가능성 낮음 (동어 반복 우려)
- **약점**: "최근 1년 내 agentic routine 보완 연구"가 누락됐을 가능성 0이 아님 — Anthropic Claude Code 자체 hook 프레임워크 발전, AutoGPT/LangGraph 회로 구조 등 후행 자료 미점검

### 주장 5 — 메모리 추가는 역효과
- **라벨**: 실증됨
- **증거**: 본 저장소 `project_opus_perception_debate.md` "빼는 안 4종" — 인덱스화·응답 형식 감축·SessionStart 컨텍스트 감축·토론 hook On-Demand화. 이미 "감산 원칙" 명시됨. 메모리 11건 이상 누적된 같은 패턴 룰이 발화 안 되는 상태에서 12번째 메모리 추가는 attention drift 악화
- **약점**: 메모리 자체가 아니라 메모리 표현·구조가 문제일 가능성 — 더 짧고 더 trigger 명확한 룰로 리팩터하면 발화율 개선 가능성 (감산 vs 리팩터 양자 미구분)

## 보완 방향 — 구체 설계 (모드 C 후보)

### Hook 1건 신설 (advisory → 1주 후 gate 전환)
- **위치**: `.claude/hooks/share_after_push.sh`
- **트리거**: PostToolUse + Bash 매처 (git push 패턴 detect)
- **동작 (advisory 단계)**: git push 직후 다음 조건 검사 — (a) 직전 commit 메시지에 `[3way]` 또는 docs(state)·feat·fix·refactor 존재, (b) `.claude/state/last_share_marker` 미존재 또는 stale → stderr 경고 1줄 + hook_log 기록. 차단 안 함
- **동작 (gate 전환 후)**: 같은 조건에서 다음 Stop hook을 차단해 share-result 미수행 시 세션 종료 못 하게 함
- **상한**: ≤30줄, 단일 파일. 기존 hook 35개 카운트는 유지(advisory는 카운트 외 분류 옵션)

### 채택 안 하는 대안
- 메모리 12번째 추가 — 주장 5 약점 인정해도 attention drift 악화 우선
- 외부 자료 추가 조사 — 주장 4 약점 인정해도 Anthropic 공식 hook 가이드는 이미 본 저장소 적용 완료(write_router_gate 선례)

## 반대 안 예상 약점 / 양측 반박 가능성
- **GPT 예상 반박**: "비중 50/20/30은 추정 — 정량 측정 없는 합의는 무의미. 클린 세션 비교 실측 선행 필요"
- **Gemini 예상 반박**: "Hook 신설 자체가 또 다른 운영 부담 — write_router_gate Day 1~7 advisory 운영도 미완료 상태에서 1건 더 추가는 인지 부하 누적"
- **공통 반박 가능성**: "메모리 리팩터(주장 5 약점)을 시도하지 않고 hook으로 직행하는 건 가장 무거운 해결책 우선 — 더 가벼운 옵션(메모리 짧게 다시 쓰기) 먼저"

## 착수·완료·검증 조건
- **착수**: pass_ratio ≥ 2/3 채택 시 모드 C 진입 + plan-first
- **완료**: hook 1건 신설 + smoke_test 케이스 1건 + write_router_gate처럼 advisory 1주 운영 후 ROI 확인 후 gate 결정
- **검증**: 다음 세션부터 commit/push 후 share-result 자동 발화율 측정. 1주 advisory 기록 후 미발화율 50% 미만이면 gate 전환, 50% 이상이면 hook 효과 부족 — 다른 안 검토 (메모리 리팩터 등)

## claude_delta 예상
- 양측 본론 수령 전이므로 partial 또는 major 가능
- GPT/Gemini가 메모리 리팩터·정량 측정 우선 등 새 관점 제시 시 partial 이상

## issue_class
- **B** — hook 신설은 시스템 흐름·판정 변경에 해당. 6-5 생략 불가, Round 2/3 가능성 열어둠
