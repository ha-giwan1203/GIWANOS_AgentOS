# plan: Claude Code Hooks 실전 패턴 적용

작성일: 2026-03-31
GPT 승인: 확인됨 (3가지 조건 포함)

---

## 수정 대상

파일: `.claude/settings.local.json` (hooks 섹션 추가)
파일: `.claude/hooks/block_dangerous.sh` (보호 파일 2계층 추가)

## GPT 조건 3건

1. PreToolUse — deny/ask 2계층
   - deny: *.xlsx, 기준정보 원본, 98_아카이브
   - ask: TASKS.md, HANDOFF.md, STATUS.md (자주 수정하므로 차단 불가)
2. PostToolUse — Edit/MultiEdit/Write만 (Bash 제외)
3. Notification — permission/idle만 전송, 중복 억제

## 기존 스크립트 재활용

| 스크립트 | 용도 | 상태 |
|---------|------|------|
| block_dangerous.sh | PreToolUse(Bash) 위험 명령 차단 | 재활용 (보호 파일 로직 추가) |
| notify_slack.sh | Notification Slack 연동 | 재활용 (스팸 방지 추가) |
| session_start.sh | SessionStart 인수인계 리마인드 | 그대로 사용 |
| session_end.sh | SessionEnd HANDOFF 갱신 리마인드 | 그대로 사용 |
| instructions_loaded.sh | InstructionsLoaded 로그 | 그대로 사용 |
| skill_config_change.sh | ConfigChange 로그 | 그대로 사용 |

## 신규 스크립트 1건

| 스크립트 | 용도 |
|---------|------|
| protect_files.sh | PreToolUse(Write/Edit) 보호 파일 2계층 판정 |

## 적용 순서

- [x] Step 1: research 완료
- [x] Step 2: GPT 승인 (조건 3건 포함)
- [x] Step 3: protect_files.sh 신규 작성 (deny/log 2계층)
- [x] Step 4: notify_slack.sh 스팸 방지 업데이트 (60초 dedup)
- [x] Step 5: settings.local.json hooks 섹션 추가 (PreToolUse 2, PostToolUse 1, Notification 1)
- [ ] Step 6: 동작 확인 (hooks 로그)
- [ ] Step 7: Git 커밋/push + GPT 보고
