# plan: 아키텍처 정리 1차 — AGENTS_GUIDE.md + SessionStart 확장

작성일: 2026-03-31
GPT 승인: 확인됨 (2건만, Slack/커밋전 검증 제외)

---

## 범위

| 항목 | 내용 |
|------|------|
| AGENTS_GUIDE.md | 6계층 아키텍처 + 구성요소 맵 + 실행 순서 문서 |
| SessionStart hook 확장 | 세션 시작 시 doc-check subagent 호출 안내 추가 |

## 제외 (후속 plan)

- Slack files:write scope (외부 권한)
- 커밋 전 task-status-sync (별도 hooks 확장)

## 적용 순서

- [x] Step 1: research 완료 (91179aa6)
- [x] Step 2: GPT plan 승인
- [ ] Step 3: AGENTS_GUIDE.md 작성
- [ ] Step 4: session_start.sh 확장
- [ ] Step 5: Git 커밋/push + GPT 보고
