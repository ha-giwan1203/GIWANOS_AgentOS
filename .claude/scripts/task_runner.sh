#!/bin/bash
# 스케줄 태스크 실행 표준화 래퍼 (세션40)
# 역할: task_id 기록 / 시작·종료 시각 / exit code / hook_task_result 호출
# 업무 로직은 각 run.py에 유지. 이 래퍼는 계측만 담당.
#
# Usage:
#   bash .claude/scripts/task_runner.sh <task_id> <command...>
#   bash .claude/scripts/task_runner.sh daily-routine python3 90_공통기준/스킬/daily-routine/run.py
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export CLAUDE_PROJECT_DIR="$PROJECT_DIR"
source "$PROJECT_DIR/.claude/hooks/hook_common.sh"

if [ $# -lt 2 ]; then
  echo "Usage: task_runner.sh <task_id> <command...>"
  exit 1
fi

TASK_ID="$1"
shift

# 시작 시각 (밀리초)
START_MS=$(python3 -c "import time; print(int(time.time()*1000))" 2>/dev/null || echo 0)

# 대상 명령 실행
set +e
OUTPUT=$("$@" 2>&1)
EXIT_CODE=$?
set -e

# 종료 시각
END_MS=$(python3 -c "import time; print(int(time.time()*1000))" 2>/dev/null || echo 0)
DURATION_MS=$((END_MS - START_MS))

# 결과 출력
echo "$OUTPUT"

# hook_task_result 호출
if [ "$EXIT_CODE" -eq 0 ]; then
  hook_task_result "$TASK_ID" "success" "exit=0" "$DURATION_MS"
else
  hook_task_result "$TASK_ID" "fail" "exit=$EXIT_CODE" "$DURATION_MS"
fi

exit "$EXIT_CODE"
