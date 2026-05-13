# Round 1 — Claude 독자 답안 (선행, NEVER 생략)

## 의제
Claude Code 떠넘기기 재발 — 자기검열(문서 규칙)만으로 불충분한가, hook gate 복원이 정당한가, 세션148 delegation_guard 폐기 결정을 뒤집어야 하는가.

## 결론 1줄
**자기검열만으로는 불충분 (H1 버림). hook gate 복원 정당 (H2 채택). 단 세션148 합의의 일부 번복만 필요 — 다른 보강(SessionStart 모드 라벨링·1줄확인 압축)과 패키지로 진행 (H3 부분 채택).**

## 주장 3개 + 라벨 + 증거

### 주장 1 [실증됨] — 문서 규칙만으로 13일 만에 재발한 것은 강도 부족의 증거
- **증거**: 세션148(2026-05-08) delegation_guard measurement 강등 → 세션157(2026-05-13) 사용자 떠넘기기 재발 체감 지적. 13일.
- **반대 안 예상 약점**: "사용자 체감 ≠ 실측 재발". 측정 로그가 없어 빈도 객관화 불가. 하지만 세션132 5회 사례 + 사용자 직접 발화는 임계 신호로 충분.
- **참조**: `feedback_authority_ladder.md` 5→2조건 축약 / `completion_gate.sh:27~33` 폐기 주석

### 주장 2 [환경미스매치] — hook gate 폐기 결정은 RLHF 본성을 과대평가
- **증거**: RLHF는 응답 안전성을 학습하지만 "자율 결정 vs 사용자 확인 요청" 사이 비대칭 — 후자가 보수적이라 학습 강화. 외부 자료(Claude Code Hook 과밀 부작용 보고, HITL escalation rate 60%+ = 시스템 미스캘리브레이션)와 일치.
- **세션148 합의 가정**: "문서 규칙 + 메모리 2조건 = 충분" — RLHF가 자기검열을 충실히 실행한다는 전제. 실측 반증됨.
- **반대 안 예상 약점**: hook gate 복원이 false positive로 토론모드 라벨링 응답까지 차단할 위험. 정규식 보수화·whitelist 필요.

### 주장 3 [구현경로미정] — gate 복원은 형태가 중요. PostResponse hook은 Claude Code에 표준 아님
- **증거**: 현재 Claude Code hook 종류 — PreToolUse / PostToolUse / UserPromptSubmit / SessionStart / Stop. 응답 출력 직전 검사 hook은 표준 아님. Stop hook이나 UserPromptSubmit 응답에 매칭 가능하지만 차단 시점 미스매치.
- **대안 1**: Claude 자신이 응답 전 self-grep (자기검열 보강)
- **대안 2**: UserPromptSubmit hook으로 사용자 발화에 "옵션 나열 의심" 키워드 감지 시 응답 강제 라벨링 요구 (간접 차단)
- **대안 3**: completion_gate에 응답 텍스트 검사 단계 추가 (현재는 commit 시점만)

## 반대 안 예상 약점
- **GPT 예상 반론**: "hook gate 복원은 세션148 합의의 토대 — 문서 규칙 강도가 부족하다고 증명되지 않음. 시그널 증폭(SessionStart 라벨링) 우선." → 반박: 13일 회귀가 실측. 시그널 증폭만으론 부족.
- **Gemini 예상 반론**: "단일 사용자 체감 발화로 합의 번복은 위험. 1주일 측정 후 결정." → 반박: 측정 메커니즘 자체가 없는 것이 세션148 결정의 결과. 닭과 달걀.

## 착수·완료·검증 조건

### 채택 시
1. **즉시 (Phase 2)**: SessionStart 모드 라벨링 hook + CLAUDE.md:73 "1줄 확인" 압축
2. **단기 (Phase 3)**: delegation_guard hook을 어떤 형태로든 gate화 — 구현 형태는 토론에서 결정 (Stop hook 텍스트 검사 / UserPromptSubmit 사전 안내 / Claude self-grep 강제 중)
3. **장기 (Phase 4)**: 세션148 합의 재검토 메모리 작성

### 검증
- hook 수정 후 PowerShell에서 금지 문구 더미 응답으로 trigger 테스트
- 1주일간 incident_ledger 매치 빈도
- false positive 5건/주 초과 시 정규식 보수화

## claude_delta 추정 (양측 본론 수령 전 추정값)
- 양측이 H1·H2·H3 전부 동의 시: `none`
- 한쪽이라도 gate 형태 대안 제시: `partial` (가능성 높음)
- 양쪽 모두 H2 거부 시: `major` (가능성 낮음)

## issue_class
**B** — hook 신설·정책 분기 변경. 6-5 종합 단계 무조건 유지 (조건 C 위반).
