#!/bin/bash
# share_after_push — git push 직후 share-result 필요 여부 advisory 알림
# 의제: debate_20260429_103117_3way Round 1 pass_ratio 1.00 (Phase B)
# 등급: advisory (차단 없음, 자동 share-result 호출 금지 — 양측 합의)
source "$(dirname "$0")/hook_common.sh"
_SAP_START=$(hook_timing_start)
INPUT_JSON=$(cat 2>/dev/null)
CMD=$(echo "$INPUT_JSON" | "$PY_CMD" -c 'import sys,json
try: d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))
except: pass' 2>/dev/null)
echo "$CMD" | grep -qE '(^|[[:space:]&;|])git[[:space:]]+push([[:space:]]|$)' || { hook_timing_end "share_after_push" "$_SAP_START" "skip_not_push"; exit 0; }
COMMIT_MSG=$(git -C "$PROJECT_ROOT" log -1 --pretty=%B 2>/dev/null)
echo "$COMMIT_MSG" | grep -qE '\[3way\]|^docs\(state\)|^feat|^fix|^refactor|^chore\(state\)' || { hook_timing_end "share_after_push" "$_SAP_START" "skip_no_share_pattern"; exit 0; }
MARKER="$PROJECT_ROOT/.claude/state/last_share_marker"
if [ -f "$MARKER" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$MARKER" 2>/dev/null || stat -f %m "$MARKER" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 300 ] && { hook_timing_end "share_after_push" "$_SAP_START" "skip_marker_fresh"; exit 0; }
fi
SHA=$(git -C "$PROJECT_ROOT" log -1 --pretty=%h 2>/dev/null)
echo "[share_after_push] git push 완료 감지 (SHA $SHA) — share-result 필요 여부 확인. [3way]/시스템 변경이면 /share-result 실행." >&2
hook_log "share_after_push" "advisory: post-push share check (SHA=$SHA)"
hook_timing_end "share_after_push" "$_SAP_START" "advisory_emitted"
exit 0
