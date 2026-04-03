#!/bin/bash
# SessionStart hook — 인수인계 읽기 순서 + doc-check 자동 호출 지시
# subagent 직접 호출은 hook에서 불가 (hook은 shell command만 실행)
# 대신 Claude에게 doc-check 실행을 강제 지시하는 메시지를 전달
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "SessionStart" "session_start 발화"
echo '{"message":"[Hook] 세션 시작 자동 점검 지시:\n1. TASKS.md → STATUS.md → HANDOFF.md 읽기\n2. /doc-check 실행하여 문서 정합성 검사 (필수)\n3. /task-status-sync 실행하여 상태 충돌 검사 (필수)\n4. 현업 업무 질문이면 업무_마스터리스트.xlsx 먼저\n5. 구조 참조: AGENTS_GUIDE.md\n위 1~3은 세션 시작 시 반드시 수행할 것. 생략 금지."}'
