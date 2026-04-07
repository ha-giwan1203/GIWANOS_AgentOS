#!/bin/bash
# Stop 전용 — GPT pending flag 존재 시 종료 차단
# gpt_followup_guard.sh에서 분리 (v2, 2026-04-06 GPT 합의)
# v3: python3→bash 전환 (#34457 Windows hooks 멈춤 대응)
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
hook_log "Stop" "gpt_followup_stop 발화" 2>/dev/null || true

INPUT=$(cat)
PENDING="$STATE_AGENT_CONTROL/gpt_followup_pending.flag"

# pending flag 없으면 통과
if [ ! -f "$PENDING" ]; then
  exit 0
fi

# 예외 보고 패턴 확인 (timeout, 로그인 만료, 검토만 등)
# bash-only JSON 파싱 (python3 의존 제거)
LAST_MSG=$(echo "$INPUT" | sed -n 's/.*"last_assistant_message"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

if echo "$LAST_MSG" | grep -qiE '(timeout|타임아웃|로그인 만료|재로그인|네트워크 오류|검토만|읽기만|예외 종료)'; then
  rm -f "$PENDING" 2>/dev/null
  exit 0
fi

# pending flag 존재 + 예외 아님 → 차단
echo '{"decision":"block","reason":"GPT 응답을 읽은 뒤 후속 작업 없이 종료할 수 없습니다. 반박/재전송 또는 합의된 실행을 먼저 진행하세요."}'
