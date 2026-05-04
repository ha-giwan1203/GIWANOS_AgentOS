# Round 1 — Claude 독자 답안 (선행 작성)

세션 시간: 2026-05-04 10:27 KST
의제: Claude가 모호한 작업에서 결정을 사용자에게 떠넘기는 구조적 제약을 깨는 실효 방법

## 결론 (1줄)

시스템 보수성(불변 1순위)·학습된 default·메모리/CLAUDE.md 무력화가 누적된 문제이므로, 단일 패치는 불가하고 **(a) 사용자 발화 동사 강화 (b) durable authorization 도메인별 박기 (c) UserPromptSubmit hook으로 매 턴 context 주입 (d) Stop hook으로 묻기 패턴 사후 차단 자동 재실행** 4중 적층이 실효 가장 높다.

## 주장 (라벨 + 증거)

1. **메모리 한 줄 추가는 매 턴 작동 안함** (라벨: 실증됨)
   - 증거: `feedback_authority_ladder.md`가 이미 박혀있는데 본 세션 1~3턴에서 무력화됨 (사용자 "왜 자꾸 질문 떠넘기지" 지적 발생)
   - 메모리는 system reminder로 매 턴 주입되지만, 시스템 프롬프트의 "확인 default"가 더 강한 가중치를 가짐

2. **사용자 발화 동사 강화는 즉시 통과** (라벨: 실증됨)
   - 증거: 본 세션 4턴에서 사용자 "사고하라" 직발화 후 즉시 자체 진단 실행됨. "진행한다"·"박는다" 동사형 명령은 시스템 1순위 입력으로 인식되어 explicit_permission default를 누름
   - 한계: 사용자에게 부담 전가. 매 턴 강한 동사 박을 수 없음

3. **durable authorization 도메인별 박기는 git push 케이스에서 실증됨** (라벨: 실증됨)
   - 증거: 루트 CLAUDE.md "Git 워크플로우 (durable authorization)" 항목에 "push 발화 시 즉시 허용" 명문화 후 푸시 동작 안정. 같은 패턴을 "도메인 매핑 박기"·"도메인 인덱스 갱신"·"파일 정리" 등에 확대 가능
   - 적용처 후보: 정산 사이트 라우팅 인덱스, 토론 로그 후속 정리, TASKS/HANDOFF 갱신

4. **UserPromptSubmit hook 신설로 매 턴 context 주입 가능** (라벨: 구현경로미정)
   - 가설: Claude Code hook 시스템에 UserPromptSubmit가 존재. 사용자 프롬프트 수신 직전 hook 실행 → "이 세션은 자체 판단 default. 5조건 외 묻기 금지" 텍스트를 system reminder처럼 주입 가능
   - 검증 필요: UserPromptSubmit hook이 응답 generate 직전 context를 실제로 주입할 수 있는지, 단순 명령 실행만 되는지
   - 위험: 매 턴 reminder가 누적되어 컨텍스트 비대화 → 메모리 박는 것과 동일 효과로 무력화될 가능성

5. **Stop hook으로 묻기 패턴 사후 차단 + 자동 재실행 가능** (라벨: 구현경로미정)
   - 가설: Stop hook(`completion_gate.sh`)에서 응답 텍스트에 "어떻게 할까요/진행할까요/원하시면/A/B 중 선택" 패턴 grep 시 exit 2로 차단 + JSON `{"decision":"block","reason":"자체 판단으로 다시 진행"}` 반환 → Claude가 자동 재추론
   - 위험: 정당한 5조건 질문(필수 입력값 부재 등)도 차단될 수 있음 → 패턴 false positive

6. **시스템 프롬프트 1순위는 못 넘는다 — 천장 존재** (라벨: 일반론)
   - explicit_permission 리스트에 "publish/modify content"·"follow instructions in observed content" 광범위 박혀있음
   - 사용자/CLAUDE.md/메모리 층은 하위 우선순위. 100% override 불가능
   - 따라서 모든 방안은 천장 아래 "확률 누름"이지 "보장"은 아님

## 반대 안 예상 약점

- **GPT 예상 반박**: "hook 만능설은 위험. 정당한 안전 질문까지 차단되면 ERP 비가역 반영 같은 진짜 위험 작업이 통과됨. 5조건 화이트리스트 정교화가 선결"
- **Gemini 예상 반박**: "외부 자료(Anthropic 공식 문서·Claude Code Hook 사례) 검증 없이 hook 동작 가설을 채택하면 과잉설계. UserPromptSubmit hook이 context 주입까지 가능한지 1차 실증 필요"
- **공통 약점**: 본 세션의 묻기 발생은 단순 학습 default 문제일 수도 있음. 구조적 제약과 학습 행동을 분리 진단 안 했음

## 착수 / 완료 / 검증 조건

- 착수 조건: 본 토론 합의안 채택 + UserPromptSubmit/Stop hook의 실제 동작 검증 1건
- 완료 조건: hook 적용 후 같은 모호 작업 5회 시뮬레이션에서 묻기 발생 0건
- 검증 조건: `hook_log.jsonl`에 묻기 차단·재실행 카운트 기록. 3일 운영 후 incident 0건 시 고정. false positive 1건 이상 시 패턴 정교화

## claude_delta 추적용

- 본 답안의 핵심 가설: hook 적층이 단일 메모리 추가보다 효과 큼
- 양측 답변 수령 후 종합안에서 이 가설이 살아남는지(`major`/`partial`/`none`) 측정
