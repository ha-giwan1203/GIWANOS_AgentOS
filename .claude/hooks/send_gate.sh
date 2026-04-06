#!/bin/bash
# PreToolUse hook — SEND GATE: ChatGPT 전송 전 미확인 응답 점검 강제
# 대상: mcp__Claude_in_Chrome__javascript_tool 호출 중 execCommand('insertText') 포함 시
# 조건: .claude/state/send_gate_passed 파일이 120초 이내에 갱신되어 있어야 통과
# GPT 합의: 2026-04-06 — 문서 규칙만으로 부족, 실행 강제 gate 필요

INPUT=$(cat)

# tool_name 추출
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data.get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

# javascript_tool이 아니면 통과
if [[ "$TOOL_NAME" != *"javascript_tool"* ]]; then
  exit 0
fi

# text 파라미터에 execCommand + insertText 패턴 확인
HAS_INSERT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    text = json.loads(data.get('tool_input', '{}')).get('text', '')
    if 'execCommand' in text and 'insertText' in text:
        print('YES')
    else:
        print('NO')
except:
    print('NO')
" 2>/dev/null)

# insertText가 아니면 통과 (일반 JS 실행은 차단하지 않음)
if [[ "$HAS_INSERT" != "YES" ]]; then
  exit 0
fi

# debate 도메인 활성 확인 — 토론모드가 아니면 통과
DEBATE_FLAG="C:/Users/User/AppData/Local/Temp/.claude_domain_debate_active"
if [ -f "$DEBATE_FLAG" ]; then
  ACTIVE_DOMAIN=$(cat "$DEBATE_FLAG" 2>/dev/null)
  if [[ "$ACTIVE_DOMAIN" != "debate" ]]; then
    exit 0
  fi
else
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# SEND GATE 파일 확인
STATE_DIR="$SCRIPT_DIR/../state"
mkdir -p "$STATE_DIR" 2>/dev/null
GATE_FILE="$STATE_DIR/send_gate_passed"

if [ ! -f "$GATE_FILE" ]; then
  echo '{"decision":"block","reason":"SEND GATE 미통과: 전송 전 미확인 응답 점검(assistant 최신 텍스트 재읽기)을 먼저 실행하세요. 점검 후 .claude/state/send_gate_passed 파일을 갱신해야 전송이 허용됩니다."}'
  exit 0
fi

# 120초 이내 갱신 확인
GATE_AGE=$(python3 -c "
import os, time
try:
    mtime = os.path.getmtime('$GATE_FILE')
    age = time.time() - mtime
    print(int(age))
except:
    print(9999)
" 2>/dev/null)

if [[ "$GATE_AGE" -gt 120 ]]; then
  echo '{"decision":"block","reason":"SEND GATE 만료('"$GATE_AGE"'초 경과): 전송 전 미확인 응답 점검을 다시 실행하세요. 120초 이내 점검만 유효합니다."}'
  exit 0
fi

# 통과 — gate 파일 삭제 (1회성)
rm -f "$GATE_FILE"
exit 0
