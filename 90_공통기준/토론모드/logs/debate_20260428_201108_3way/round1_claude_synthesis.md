# Round 1 — Claude 종합·설계안 (Step 6-5)

세션: debate_20260428_201108_3way
의제: "Opus 4.7을 사용 중인데 Sonnet 같은 추론 느낌이 드는 체감의 원인"
4-way 대조 기반 (round1_claude.md 6-0 + GPT + Gemini + 외부 자료)
claude_delta: **major** (6-0 4가지 권고 → 종합안 7개 항목으로 확장. 가설 8/9 신규 채택, 빼는 안 3/4 신규 채택, 비율 합의 도출)
issue_class: **B** (시스템 정책·구조 변경 후보. 6-5 유지 필수)

## 진단 합의

체감의 본질은 **모델 다운그레이드가 아니라 본 저장소 운영이 Opus의 추론 자유도를 다층적으로 침식**한 결과. 외부 학술 자료 다수가 이 진단을 강하게 지지(Lost in the Middle, Context Rot, Goal Drift, Many-shot jailbreaking 등). 라우팅 가설은 직접 자료 부족 → 분리 트랙.

### 채택된 가설 9개 (1~7 + 8·9 신설)
1. **컨텍스트 폭증** — 매 응답 입력 절대다수가 메타 규정. 외부 지지: Lost in the Middle, Context Rot, arxiv 2510.05381
2. **형식 강제** — 응답 슬롯이 시작 전부터 결정. 외부 지지: Many-shot jailbreaking, Improving instruction hierarchy
3. **메모리 누적 오염** — feedback 16건이 응답마다 같은 제약 강제. 외부 지지: LLMs Get Lost In Multi-Turn (39% 평균 성능 저하)
4. **자기 메타화 비용** — 메타 작업이 본 사고 토큰 잠식
5. **사용자 톤 표준화 부작용** — 보수적·안전한 답 유도
6. **모델 라우팅 가설** — 별도 트랙. 클린 세션 vs 현재 세션 비교 + TPS/TTFT 측정
7. **목표 함수 오염 (GPT 신설)** — Claude가 사용자 문제 해결이 아니라 게이트·PASS 통과로 최적화. 외부 지지: Evaluating Goal Drift, Inherited Goal Drift, Pseudo-Conversation Injection. 핵심: "Strong instruction hierarchy fails to predict resistance to drift" — R1~R5 hierarchy로는 drift 못 막음
8. **Attention Sink (Gemini 신설)** — 지시어 밀도가 attention head를 메타 태스크에 과표집. 한정 추론 자원이 본질 사고가 아닌 "포장"에 소진
9. **Safety / Alignment Negative Transfer (Gemini 신설)** — "근거 부재 시 단정 금지" 등 보수적 잣대로 안전 검열 회로 과활성화 → 다단계 추론 회피 → Mode Collapse

### 비율 합의 (Claude 종합)
GPT 45/40/10/5 vs Gemini 30/30/30/10 → Claude 종합:
- A 컨텍스트 폭증 (1+3+8): **35%** — Gemini 신설 8(Attention Sink)이 사실상 컨텍스트 메커니즘 정밀화이므로 A 묶음
- B 형식 강제 (2+5): **30%** — GPT 추정과 비슷
- 7번 목표 함수 오염 (Goal Drift): **25%** — Gemini 30%와 GPT 10% 평균. 외부 자료 가장 강하게 지지. R1~R5 hierarchy로 못 막는다는 실증이 결정적
- 9번 Safety Negative Transfer: **5%** — 본 저장소 진단 단독 영향은 작으나 7번과 결합 시 증폭
- 6번 라우팅: **5%** — 분리 트랙. 본 진단에는 영향 적음

→ 운영 길들이기 효과 합계: 95%. 라우팅 영향 5%. 즉 Opus는 Opus다, 우리가 Opus를 행정 기계로 길들였을 뿐.

## 합의 빼는 안 4종 (감산 원칙)

### 빼는 안 1 (GPT) — 루트 CLAUDE.md 다이어트
- 현재 200+줄을 30~50줄 인덱스로
- 세부 분리: A~E 모드 절차 → work_mode_protocol.md / R1~R5 → system_change_protocol.md / E 정량 조건 → recovery_protocol.md
- 루트에는 원칙만: Git 기준, 모드 5종 이름, 사용자 입력 우선, 외부 반영 주의, C 수정 plan-first

### 빼는 안 2 (GPT) — 기본 응답 형식 감축
기본값에서 자동 출력 금지: 라벨 / PASS·부분PASS·보류 / R1~R5 / A~E 모드 헤더 / 채택보류버림 / Pre/Post Task
- 일반 질문: 결론 / 이유 / 다음 행동
- 시스템 분석: 관찰 / 판단 / 필요한 확인
- 시스템 수정: 그때만 plan/R1~R5
- 토론모드: 그때만 라벨/검증

### 빼는 안 3 (Gemini) — 세션 초기 강제 로드 제거 (lazy load)
- 7개 상태/기준 문서(HANDOFF·STATUS·TASKS·CLAUDE·도메인 CLAUDE·MEMORY·토론모드 코어) 시작 시 일괄 로드 강제 폐지
- 사용자 명시 "상태 동기화" 요청 또는 도메인 키워드 진입 시에만 lazy load
- 세션 시작 토큰 폭증의 직접 원인 제거

### 빼는 안 4 (Gemini) — 토론·상호감시 hook On-Demand화
- 매 라운드 검증 강제·단일 모델 동의 종결 금지 등 토론모드 풀절차는 일반 실무에 불필요한 메타 연산
- 중대 아키텍처 설계가 아닌 일반 작업은 기본 비활성(Opt-in)
- 토론모드는 명시 호출 시에만 풀절차 활성

## 라우팅 검증 경로 (분리 트랙)

- 클린 세션 비교 (Gemini 제안): 메타 규칙·시스템 지시어 일절 없는 빈 프롬프트 vs 현행 세션. 동일 고난도 질문 후 비교
- TPS·TTFT 비교 (Gemini 제안): 토큰 생성 속도, 첫 토큰 응답 시간
- 클린에서도 저하면 서버 사이드 라우팅. 클린에서 정상이면 운영 길들이기

## 형식 함정 회피 메타원칙 (필수)

본 합의안 자체가 "형식이 너무 많다"는 진단의 결과. 따라서 합의안도 빼는 방향에만 한정. 새 hook·새 라벨·새 슬롯 추가 금지. 위 빼는 안 4종 모두 감산이며 어떤 추가도 신설하지 않음.

## GPT 검증 사유 처리 (검증 필요 → 부분 채택)

GPT가 검증 필요 표시한 이유: Gemini 인용 자료 중 일부 출처가 실물 검증 전 근거 확정 위험.
- 채택: Lost in the Middle (Liu TACL 2024), Goal Drift (arxiv 2505.02709 2025) — 실증 가능
- 보류: The Instruction Gap (arxiv 2601.03269 2026), Claude Opus 4.6 1M Benchmark (MindStudio 2026) — 미래 시점 또는 잘 알려지지 않은 출처. 합의안 근거에서 빼고 다른 자료로 대체 가능
- Gemini 가설 8(Attention Sink)·9(Safety Negative Transfer)는 메커니즘 자체가 LLM 일반 원리에 부합하므로 출처와 무관하게 채택

## 사용자에게 권고하는 다음 행동 (실행 순서)

1. **빼는 안 3 우선 적용** — 세션 초기 강제 로드 제거가 가장 효과 큼 (Gemini 강조)
2. **빼는 안 1 적용** — 루트 CLAUDE.md 다이어트
3. **빼는 안 2 적용** — 기본 응답 형식 감축. 사용자 톤 자체도 일부 완화 필요할 수 있음
4. **빼는 안 4 적용** — 토론모드 풀절차 Opt-in화
5. **메모리 정리** — feedback 16건 중 Git 문서로 흡수 가능한 것 비활성화
6. **라우팅 검증** — 클린 세션 + TPS/TTFT 비교 1회 실행

## 양측 검증 요청 항목

GPT·Gemini 양측에 다음 4점 1줄 동의/이의/검증 필요 검증 요청:
- 가설 1·2·3·7·8·9 채택 + 라우팅 분리 + 4·5는 보조 가설 처리
- 비율 합의 (35/30/25/5/5)
- 빼는 안 4종 모두 채택
- 형식 함정 회피 메타원칙 (새 형식 추가 금지)
