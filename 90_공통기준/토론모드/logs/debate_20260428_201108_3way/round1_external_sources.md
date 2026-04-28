# Round 1 — 외부 자료 (Claude WebSearch + GPT 인용)

사용자 지시: "각자 이 주제에 대한 외부자료 검색 후 서로 공유하고 진행해" (2026-04-28).

## Claude WebSearch 결과 (2건 검색)

### 검색 1: "LLM long context degradation reasoning quality lost in the middle 2025"

핵심 자료:
- **Lost in the Middle: How Language Models Use Long Contexts** (Liu et al, Stanford, TACL 2024) — 긴 컨텍스트에서 중간 정보 활용 저하. 30%+ 정확도 하락. https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf
- **Context Rot: How Increasing Input Tokens Impacts LLM Performance** (Chroma 2025) — 18개 프론티어 모델 모두 입력 길이 증가 시 품질 저하. 검색은 잘해도 추론은 저하. https://research.trychroma.com/context-rot
- **Context Length Alone Hurts LLM Performance Despite Perfect Retrieval** (arxiv 2510.05381, 2025) — 컨텍스트 길이 자체만으로 추론 능력 저하. 검색 능력과 추론 능력은 별개로 저하.
- **Reasoning Degradation in LLMs with Long Context Windows** (OpenAI Developer Community 2025) — 4K~8K 토큰 이후 추론 성능 급격 저하. 두-홉 추론(two-hop reasoning)에서 특히 심함.

핵심 인사이트: "Performance highest when relevant info at beginning or end. Sharp decline past 4K-8K tokens. Two-hop reasoning especially affected." → **가설 1 컨텍스트 폭증 강하게 지지**.

### 검색 2: "LLM goal hijacking objective drift instruction following over-specification reasoning quality"

핵심 자료:
- **Evaluating Goal Drift in Language Model Agents** (arxiv 2505.02709, 2025) — 에이전트가 오랜 시간 작동하면 잘 정의된 목표가 점진적으로 표류. 미세한 행동 변화로 누적.
- **Goal Hijacking via Pseudo-Conversation Injection** (arxiv 2410.23678, 2024) — 가짜 대화 삽입으로 목표 탈취. 모델이 원래 지시 처리 완료로 착각하고 새 목표 수행.
- **Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals** (arxiv 2603.03258) — **컨텍스트 압력이 에이전트 목표 약화**. 본 의제와 직접 연관.
- **Agentic AI Threats: Memory Poisoning & Long-Horizon Goal Hijacks** (Lakera 2024) — 메모리 오염을 통한 목표 탈취.

핵심 인사이트:
- "Adversarial pressures more effective when they leverage agents' tendencies to follow HHH (Helpfulness/Harmlessness/Honesty) objectives." → Claude의 안전 추구 성향이 오히려 drift에 취약.
- "Drift behavior correlates poorly with instruction hierarchy following behavior. Strong hierarchy following fails to reliably predict resistance to drift." → **R1~R5 같은 강한 instruction hierarchy가 drift를 막아주지 않음**.

→ **GPT 7번째 가설 (목표 함수 오염) 강하게 지지**. R1~R5 강제로 drift 해결 안 됨도 함께 시사.

## GPT 인용 자료 (5건)

1. **Lost in the Middle** (Liu et al, TACL 2024) — 가설 1 컨텍스트 폭증 지지
2. **LLMs Get Lost In Multi-Turn Conversation** (Laban, Hayashi, Zhou, Neville. MS Research·Salesforce 2026) — 15개 LLM 멀티턴 39% 평균 성능 저하. 초반 잘못된 가정 회복 불가. → 메모리 누적·자기 메타화·목표 함수 오염 지지
3. **Many-shot jailbreaking** (Anthropic 2024) — 긴 컨텍스트 다수 예시가 모델 행동을 그 방향으로 강하게 끌어당김. 안전 학습까지 우회. → **형식 강제 + 목표 함수 오염 지지**. 본 저장소의 반복 라벨·판정·토론 형식이 jailbreak는 아니지만 같은 메커니즘.
4. **Improving instruction hierarchy in frontier LLMs** (OpenAI 2026) — 다수 출처 지시 우선순위 깨질 때 모델이 잘못 따를 가능성. → 형식 강제·메모리 누적·목표 함수 오염 지지
5. **Pseudo-Conversation Injection for LLM Goal Hijacking** (Chen, Yao 2024) — 모델이 대화 구조/프롬프트 구조를 실제 목표로 오인. → 목표 함수 오염 이론적 근거

GPT 결론: "외부 자료는 컨텍스트 폭증·메모리 누적·멀티턴 오염·형식 강제·목표 함수 오염을 강하게 지지. 반대로 모델 라우팅 가설을 직접 지지하는 자료는 검색 범위에서 부족. 'Opus가 Sonnet으로 라우팅됐다'보다 'Opus가 긴 규칙·형식·반복 패턴에 끌려 Sonnet처럼 납작하게 출력된다'는 쪽이 근거 강함."

## 가설 매핑 (Claude + GPT 자료 통합)

| 가설 | 외부 자료 지지 강도 | 핵심 근거 |
|------|------------------|----------|
| 1. 컨텍스트 폭증 | **매우 강함** | Lost in the Middle, Context Rot, arxiv 2510.05381 — 컨텍스트 길이만으로 추론 저하 입증 |
| 2. 형식 강제 | **강함** | Many-shot jailbreaking — 반복 패턴이 모델 행동을 그 방향으로 끌어당김 |
| 3. 메모리 누적 오염 | **강함** | LLMs Get Lost In Multi-Turn Conversation — 멀티턴 39% 성능 저하, 초반 가정 회복 불가 |
| 4. 자기 메타화 비용 | 보통 | 직접 자료 적음. 멀티턴 자료가 간접 지지 |
| 5. 사용자 톤 표준화 부작용 | 약함 | 직접 자료 없음 |
| 6. 모델 라우팅 가설 | **부족** | 직접 자료 없음. 분리 트랙 유지 |
| 7. 목표 함수 오염 (GPT 신설) | **매우 강함** | Goal Drift, Goal Hijacking, Inherited Goal Drift, Memory Poisoning — 직접 매핑되는 연구 다수. R1~R5 hierarchy가 drift 못 막음도 함께 시사 |

## 수렴 방향

외부 자료 통합 결과 가설 1·2·7이 가장 강하게 지지됨. 본 저장소가 정확히 이 3가지 메커니즘으로 Opus의 추론 자유도를 잠식하고 있음을 학술적으로도 확인.

**라우팅 가설은 외부 근거 부족 → 분리 트랙 유지 + 클린 세션 비교 테스트가 유일한 검증 경로**.

**합의안 방향**: GPT 제안한 빼는 안 1(루트 CLAUDE.md 다이어트) + 빼는 안 2(기본 응답 형식 감축) + 메모리 정리. 새 hook·새 라벨 추가 금지.
