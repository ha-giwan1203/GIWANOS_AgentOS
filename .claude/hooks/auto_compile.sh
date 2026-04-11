#!/bin/bash
# auto-compile: .py 파일 편집 후 즉시 문법 검증 (동기, 블로킹)
# PostToolUse(Write|Edit) 매처로 실행
# 합의: GPT+Claude 2026-04-01 — 문법 검사는 동기, 알림/로깅만 async

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT=$(cat)
# safe_json_get 사용 (python3 JSON 파싱 대체, GPT+Claude 합의 2026-04-11)
FILE_PATH=$(echo "$INPUT" | safe_json_get "file_path" 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | safe_json_get "path" 2>/dev/null)
fi

# python3/python 동적 감지
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
fi

# .py 파일만 대상
if [[ "$FILE_PATH" == *.py ]] && [ -n "$PY_CMD" ]; then
  if [ -f "$FILE_PATH" ]; then
    RESULT=$($PY_CMD -m py_compile "$FILE_PATH" 2>&1)
    if [ $? -ne 0 ]; then
      hook_incident "compile_fail" "auto_compile" "$FILE_PATH" "$RESULT" '"classification_reason":"compile_fail"' 2>/dev/null || true
      echo "{\"message\":\"[COMPILE FAIL] $FILE_PATH 문법 오류: $RESULT\"}"
      exit 2  # Claude에게 수정 요청
    fi
  fi
fi

exit 0
