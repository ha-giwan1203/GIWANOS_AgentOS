#!/bin/bash
# auto-compile: .py 파일 편집 후 즉시 문법 검증 (동기, 블로킹)
# PostToolUse(Write|Edit) 매처로 실행
# 합의: GPT+Claude 2026-04-01 — 문법 검사는 동기, 알림/로깅만 async

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: advisory (Phase 2-C 2026-04-19 세션73 timing 배선)
# 주의: compile_fail 시 exit 2 유지 (기존 동작) — advisory 등급이지만 컴파일 실패는 상위 도구에 알려야 함
_AC_START=$(hook_timing_start)

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
      hook_timing_end "auto_compile" "$_AC_START" "compile_fail"
      exit 2  # Claude에게 수정 요청
    fi
    hook_timing_end "auto_compile" "$_AC_START" "compile_ok"
    exit 0
  fi
fi

hook_timing_end "auto_compile" "$_AC_START" "skip_nonpy"
exit 0
