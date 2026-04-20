#!/bin/bash
# share_gate — share-result 0단계 3way 감지 조건 자동 검증
# 세션79 실증 (2026-04-20): "hook/settings 신설 커밋인데 2자 경로 선택" 우회 차단
# 등급: advisory (차단은 하지 않음, stderr 경고 + hook_log 기록)
# 호출: share-result 스킬 진입 시 수동 실행 (또는 /share-result 커스텀 hook에서)

source "$(dirname "$0")/hook_common.sh"
_SG_START=$(hook_timing_start)

# 공유 대상 커밋: 기본 HEAD (share-result는 최신 커밋을 공유)
COMMIT="${SHARE_GATE_COMMIT:-HEAD}"
REASONS=()

# 조건 1: [3way] 태그
if git log -1 --pretty=%B "$COMMIT" 2>/dev/null | grep -q '\[3way\]'; then
  REASONS+=("[3way] 태그 커밋")
fi

# 조건 2: 이번 세션 debate-mode 호출 (당일 3way 로그 디렉토리)
TODAY=$(date '+%Y%m%d')
if ls -d "$PROJECT_ROOT/90_공통기준/토론모드/logs/debate_${TODAY}_"*"_3way" 2>/dev/null | head -1 | grep -q .; then
  REASONS+=("당일 3way 토론 로그 존재")
fi

# 조건 3: 직전 5커밋 [3way] 미종결 (간이 판정 — [3way] 태그 커밋 이후 Gemini PASS 기록 없음)
PREV_3WAY=$(git log -5 --pretty=%H "$COMMIT" 2>/dev/null | tail -4 | while read sha; do
  git log -1 --pretty=%B "$sha" 2>/dev/null | grep -q '\[3way\]' && echo "$sha"
done | head -1)
if [ -n "$PREV_3WAY" ]; then
  # Gemini PASS 기록이 이후 커밋에 있는지 확인 (간이)
  if ! git log "$PREV_3WAY..$COMMIT" --pretty=%B 2>/dev/null | grep -qiE 'gemini.*PASS|Gemini.*동의|양측.*PASS'; then
    REASONS+=("직전 5커밋 내 [3way] 미종결 의심 ($PREV_3WAY)")
  fi
fi

# 조건 4 [세션79 신설]: 공유 대상 커밋이 hook 신설·삭제 또는 settings 구조 변경 포함
CHANGED=$(git diff --name-status "${COMMIT}~1..${COMMIT}" 2>/dev/null)
HOOK_CHANGE=$(echo "$CHANGED" | grep -E '^[AD]\s+\.claude/hooks/.*\.sh$')
SETTINGS_CHANGE=$(echo "$CHANGED" | grep -E '\.claude/settings.*\.json$')
if [ -n "$HOOK_CHANGE" ]; then
  HOOK_FILES=$(echo "$HOOK_CHANGE" | awk '{print $2}' | tr '\n' ' ')
  REASONS+=("hook 신설/삭제: $HOOK_FILES")
fi
if [ -n "$SETTINGS_CHANGE" ]; then
  # 단순 값 토글 vs 구조 변경 간이 판별: permissions/hooks 블록 줄수 변동이 5줄 이상이면 구조 변경
  STRUCT_LINES=$(git diff "${COMMIT}~1..${COMMIT}" -- .claude/settings.json 2>/dev/null | grep -cE '^[+-]\s*"(permissions|hooks)"|^[+-]\s*"(allow|deny|PreToolUse|PostToolUse|SessionStart)"' || echo 0)
  if [ "$STRUCT_LINES" -ge 2 ] 2>/dev/null; then
    REASONS+=("settings.json 구조 변경 감지")
  fi
fi

# 판정
if [ ${#REASONS[@]} -gt 0 ]; then
  echo "[share_gate] 3way 공유 필수 — 감지 사유 ${#REASONS[@]}건:" >&2
  for r in "${REASONS[@]}"; do
    echo "  - $r" >&2
  done
  echo "[share_gate] → GPT 공유 후 Gemini에도 동일 메시지 전송 필수. 2자 종결 금지." >&2
  hook_log "share_gate" "3way required: ${REASONS[*]}"
  hook_timing_end "share_gate" "$_SG_START" "3way_required"
else
  echo "[share_gate] 2way 허용 (3way 감지 조건 0건)" >&2
  hook_log "share_gate" "2way ok"
  hook_timing_end "share_gate" "$_SG_START" "2way_ok"
fi

exit 0
