# research: 업무 자동화 아키텍처 정리 (B등급 1번)

작성일: 2026-03-31
목적: 현재 분산된 자동화 조각들을 계층 아키텍처로 정리

---

## 1. 현재 프로젝트 자동화 구성요소

| 계층 | 구성요소 | 역할 |
|------|---------|------|
| 실행 계층 | skills (7종) | 반복 업무 자동화 (라인배치, 정산, ZDM 등) |
| 검증 계층 | commands (3종) | doc-check, task-status-sync, review-claude-md |
| 검증 계층 | hooks (4종) | PreToolUse 보호, PostToolUse 로그, Notification |
| 검증 계층 | 하네스 3인 체제 | Planner→Generator→Evaluator |
| 감시 계층 | watch_changes.py (Phase 1~6) | 파일 감지→커밋→상태갱신→Slack→Notion→스킬설치 |
| 상태 계층 | TASKS/STATUS/HANDOFF | 상태 원본 + 재개 위치 + 세션 메모 |
| 협업 계층 | GPT 공동작업 | research→plan→구현→GPT 검증 |
| 현업 계층 | 업무_마스터리스트.xlsx | 현업 업무 원본 (AI 작업과 분리) |

## 2. 아키텍처 패턴 대응 (외부 리소스 기반)

| 패턴 | 현재 상태 | 개선 여지 |
|------|---------|----------|
| Sequential Pipeline | watch_changes Phase 1→6 | 이미 구현됨 |
| Hierarchical Multi-Agent | subagent 파일럿 2종 | 확대 가능 (commands→subagent 승격) |
| Spec-Driven Development | CLAUDE.md + Plan-First 워크플로우 | 이미 운영 중 |
| Deterministic Orchestration | hooks + allowlist/blocklist | 이미 운영 중 |
| Automated Evaluation | 하네스 Evaluator + GPT 검증 | 이미 운영 중 |

## 3. 현재 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────┐
│                  현업 계층                        │
│  업무_마스터리스트.xlsx (현업 업무 원본)            │
└──────────────────┬──────────────────────────────┘
                   │ 참조
┌──────────────────▼──────────────────────────────┐
│                  상태 계층                        │
│  TASKS.md ← STATUS.md ← HANDOFF.md              │
│  (상태 원본)  (운영 요약)  (세션 메모)              │
└──────────────────┬──────────────────────────────┘
                   │ 기준
┌──────────────────▼──────────────────────────────┐
│                  협업 계층                        │
│  Claude ←→ GPT (research→plan→구현→검증)          │
│  CLAUDE.md (운영 원칙) + Plan-First 워크플로우      │
└──────────────────┬──────────────────────────────┘
                   │ 제어
┌──────────────────▼──────────────────────────────┐
│                  검증 계층                        │
│  hooks (PreToolUse/PostToolUse)                   │
│  commands→subagent (doc-check, task-status-sync)  │
│  하네스 3인 체제 (Planner→Generator→Evaluator)     │
└──────────────────┬──────────────────────────────┘
                   │ 실행
┌──────────────────▼──────────────────────────────┐
│                  실행 계층                        │
│  skills: 라인배치, 정산, ZDM, xlsx, docx 등        │
│  스크립트: 정산파이프라인, BI복사 등                │
└──────────────────┬──────────────────────────────┘
                   │ 감시
┌──────────────────▼──────────────────────────────┐
│                  감시 계층                        │
│  watch_changes.py → commit_docs → status_update   │
│  → slack_notify → notion_sync → skill_install     │
└─────────────────────────────────────────────────┘
```

## 4. 빠진 것 (개선 후보)

| 항목 | 현재 | 개선안 |
|------|------|-------|
| 세션 시작 자동 검증 | 수동 (/doc-check 실행) | hooks SessionStart에서 subagent 자동 호출 |
| 커밋 전 자동 검증 | 수동 | PreToolUse(Bash) git commit 감지 시 task-status-sync 실행 |
| Slack 보고 PNG 첨부 | files:write scope 미해결 | Bot Token scope 추가 |
| 에이전트 거버넌스 문서 | 없음 | AGENTS_GUIDE.md 신설 (구성요소 맵 + 실행 순서) |

## 5. 제안: 다음 단계

1. **AGENTS_GUIDE.md 신설** — 위 아키텍처 다이어그램 + 각 계층 구성요소 맵
2. **SessionStart hook 확장** — doc-check subagent 자동 호출
3. **files:write scope 해결** — Slack Bot Token 갱신

---

Sources:
- [Vellum AI: Agentic Workflows 2026](https://vellum.ai/blog/agentic-workflows-emerging-architectures-and-design-patterns)
- [StackAI: 2026 Guide to Agentic Workflow Architectures](https://www.stackai.com/blog/the-2026-guide-to-agentic-workflow-architectures)
- [Google Cloud: Agentic AI Design Patterns](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [Microsoft: AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
