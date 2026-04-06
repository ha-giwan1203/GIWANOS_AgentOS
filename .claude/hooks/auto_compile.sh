#!/bin/bash
# auto-compile: .py 파일 편집 후 즉시 문법 검증 (동기, 블로킹)
# PostToolUse(Write|Edit) 매처로 실행
# 합의: GPT+Claude 2026-04-01 — 문법 검사는 동기, 알림/로깅만 async

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('tool_input',{}).get('path',''))" 2>/dev/null)

# .py 파일만 대상
if [[ "$FILE_PATH" == *.py ]]; then
  if [ -f "$FILE_PATH" ]; then
    RESULT=$(python3 -m py_compile "$FILE_PATH" 2>&1)
    if [ $? -ne 0 ]; then
      hook_incident "compile_fail" "auto_compile" "$FILE_PATH" "$RESULT" 2>/dev/null || true
      echo "{\"message\":\"[COMPILE FAIL] $FILE_PATH 문법 오류: $RESULT\"}"
      exit 2  # Claude에게 수정 요청
    fi
  fi
fi

exit 0
