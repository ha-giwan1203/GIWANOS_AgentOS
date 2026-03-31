# research: 멀티에이전트 오케스트레이션 (A등급 2번)

작성일: 2026-03-31
출처: Claude Code 공식 문서 + 외부 리소스

---

## 1. subagents vs agent teams 비교

| 항목 | Subagents | Agent Teams |
|------|-----------|-------------|
| 컨텍스트 | 별도 창, 결과만 메인으로 반환 | 별도 창, 완전 독립 |
| 통신 | 메인 에이전트에게만 보고 | 팀원끼리 직접 메시지 |
| 조율 | 메인이 모든 작업 관리 | 공유 task list + 자율 조정 |
| 적합한 작업 | 결과만 필요한 집중 작업 | 토론/협업이 필요한 복잡 작업 |
| 토큰 비용 | 낮음 (결과 요약만) | 높음 (각 팀원이 별도 Claude 인스턴스) |
| 상태 | 정식 기능 | 실험 기능 (기본 비활성) |

## 2. 우리 프로젝트 판정: subagents로 충분

### 현재 자동화 대상 3가지

| 작업 | 성격 | 팀원 간 토론 필요? |
|------|------|-------------------|
| 상태 판정 (TASKS/STATUS/HANDOFF 충돌 검사) | 결과만 받으면 됨 | X |
| 계획 검토 (research/plan 형식 검증) | 결과만 받으면 됨 | X |
| Git 실물 검증 (커밋 diff 확인) | 결과만 받으면 됨 | X |

3가지 모두 "결과만 필요한 집중 작업" → **subagents 적합**

### agent teams가 필요한 경우 (현재 해당 없음)

- 경쟁 가설 디버깅 (서로 논박)
- 병렬 코드 리뷰 (보안/성능/테스트 각각)
- 새 기능 병렬 개발 (프론트/백/테스트 분리)

## 3. 이미 존재하는 커맨드와의 매핑

| 기존 커맨드 | subagent 역할 | 승격 방법 |
|------------|--------------|----------|
| `/doc-check` | 문서 정합성 검사 에이전트 | Agent tool로 실행 |
| `/task-status-sync` | 상태 충돌 탐지 에이전트 | Agent tool로 실행 |
| `/review-claude-md` | CLAUDE.md 규칙 검토 에이전트 | Agent tool로 실행 |

커맨드 → subagent 승격은 별도 코드 없이 프롬프트만으로 가능:
```
Agent tool (subagent_type=Explore) → /doc-check 내용 실행 → 결과 반환
```

## 4. GPT-Claude 수동 협업 자동화 가능 범위

| 현재 (수동) | 자동화 가능 | 방법 |
|------------|-----------|------|
| Claude 작업 → push → GPT에 보고 | 유지 (GPT는 외부 시스템) | 변경 불가 |
| GPT 검증 → PASS/FAIL | 유지 | GPT API 없으면 수동 유지 |
| Claude research → GPT 승인 → plan → 구현 | research/plan 자동 형식 검증만 subagent로 | `/review-claude-md` 활용 |

결론: GPT 자체를 자동 에이전트로 전환하는 건 현재 구조에서 불가 (GPT는 브라우저 경유만 가능). subagent로 할 수 있는 건 **내부 품질 검증 자동화**까지.

## 5. 제안: 최소 적용안

1. 세션 시작 시 `/doc-check`를 subagent로 자동 실행 → 문서 정합성 사전 확인
2. 커밋 전 `/task-status-sync`를 subagent로 자동 실행 → 상태 충돌 사전 탐지
3. agent teams는 보류 (실험 기능, 토큰 비용 高, 현재 작업 성격에 불필요)

---

## 판정

subagents: 적용 가능 (기존 커맨드 3종 활용)
agent teams: 보류 (실험 기능, 현재 불필요)

Sources:
- Claude Code 공식: https://code.claude.com/docs/en/agent-teams
- Claude Code 공식: https://code.claude.com/docs/en/sub-agents
