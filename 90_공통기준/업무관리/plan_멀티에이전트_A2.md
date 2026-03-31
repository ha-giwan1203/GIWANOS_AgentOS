# plan: 멀티에이전트 파일럿 — subagent 2종

작성일: 2026-03-31
GPT 승인: 확인됨 (최소 파일럿 2종)

---

## 범위

| subagent | 역할 | 기존 커맨드 |
|----------|------|-----------|
| doc-check | TASKS/STATUS/HANDOFF/CLAUDE.md 정합성 검사 | `/doc-check` |
| task-status-sync | TASKS↔STATUS↔HANDOFF 상태 충돌 탐지 | `/task-status-sync` |

## 적용 방식

기존 `.claude/commands/` 커맨드를 `.claude/agents/`로 이식하지 않고,
현재 Agent tool의 `subagent_type` 파라미터로 호출하는 방식 사용.

이유: `.claude/agents/`는 공식 문서 기준이나, 현재 프로젝트는 commands 체계가 이미 운영 중.
기존 커맨드 내용을 Agent tool 프롬프트로 전달하면 동일 효과.

## 적용 순서

- [x] Step 1: research 완료 (0e0bf1d2)
- [x] Step 2: GPT plan 승인
- [ ] Step 3: doc-check subagent 테스트 실행 + 결과 확인
- [ ] Step 4: task-status-sync subagent 테스트 실행 + 결과 확인
- [ ] Step 5: Git 커밋/push + GPT 보고

## 제약

- agent teams 사용 안 함 (실험 기능, 과함)
- 기존 커맨드 파일 수정 없음
- 새 파일 생성 최소화
