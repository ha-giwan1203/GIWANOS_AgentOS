#!/bin/bash
# AGENTS_GUIDE.md 인벤토리 자동갱신 스크립트
# 마커 블록(<!-- AUTO_HOOKS_START/END -->, <!-- AUTO_SKILLS_START/END -->)만 갱신
# 아키텍처 서술은 보존
# 세션52 GPT 합의: hooks목록 + skills목록 + grade 표만 자동화

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
SETTINGS_TEAM="$PROJECT_DIR/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_DIR/.claude/settings.local.json"
SKILL_DIR="$PROJECT_DIR/90_공통기준/스킬"
GUIDE="$PROJECT_DIR/90_공통기준/업무관리/AGENTS_GUIDE.md"
README="$PROJECT_DIR/.claude/hooks/README.md"

# Python fallback (doctor_lite.sh 선례 — Windows/경량 환경 대응)
PY_CMD="python"
command -v python3 >/dev/null 2>&1 && PY_CMD="python3"

if [ ! -f "$GUIDE" ]; then
  echo "[ERROR] AGENTS_GUIDE.md not found: $GUIDE"
  exit 1
fi

# --- hooks 목록 생성 ---
# 파싱 SSoT: parse_helpers.py hooks_from_settings (team+local union)
# 세션98 M3/M4 선례 재사용. Windows \r 이슈 대비 tr -d '\r '
if [ ! -f "$SETTINGS_TEAM" ] && [ ! -f "$SETTINGS_LOCAL" ]; then
  echo "[WARN] settings files missing: $SETTINGS_TEAM / $SETTINGS_LOCAL" >&2
  HOOK_COUNT=0
else
  HOOK_COUNT=$("$PY_CMD" "$PROJECT_DIR/.claude/scripts/parse_helpers.py" --op hooks_from_settings \
    --path "$SETTINGS_TEAM" \
    --path "$SETTINGS_LOCAL" 2>/dev/null \
    | "$PY_CMD" -c "import json,sys;print(json.load(sys.stdin).get('total',0))" 2>/dev/null \
    | tr -d '\r ')
  [ -z "$HOOK_COUNT" ] && HOOK_COUNT=0
fi

# README에서 활성 훅 표 추출: 현재 README의 3열 표(`훅 | matcher | 역할`) 기준
HOOKS_ROWS=""
if [ -f "$README" ]; then
  while IFS= read -r line; do
    hook=$(printf '%s\n' "$line" | grep -oE '`[a-z_]+\.sh`' | head -1)
    [ -z "$hook" ] && continue
    role=$(printf '%s\n' "$line" | awk -F'|' '{print $(NF-1)}' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -z "$role" ] && role=$(printf '%s\n' "$line" | awk -F'|' '{print $NF}' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -n "$role" ] && HOOKS_ROWS="${HOOKS_ROWS}| ${hook} | ${role} |
"
  done < <(sed -n '/^## 활성 Hook/,/^## 핵심 운영 원칙/p' "$README" | grep '^\|')
fi

# README의 각 층별 표에서 .sh 행 추출 + 층 라벨 부착
HOOKS_BLOCK="### Hooks (.claude/hooks/) — ${HOOK_COUNT}개 활성 (settings.json+settings.local.json 기준)

> 상세: \`.claude/hooks/README.md\` 참조. 아카이브: \`.claude/hooks/_archive/\`
> 이 섹션은 \`generate_agents_guide.sh\`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스크립트 | 역할 |
|---------|------|
${HOOKS_ROWS}"

# --- skills 목록 생성 ---
SKILL_ROWS=""
SKILL_COUNT=0
for skill_md in "$SKILL_DIR"/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  dir=$(dirname "$skill_md")
  name=$(basename "$dir")
  grade=$(grep -m1 'grade:' "$skill_md" 2>/dev/null | sed 's/.*grade:[[:space:]]*//' | tr -d ' ')
  # description 첫 줄만 (멀티라인 > 제거)
  # v2 (debate_20260428_110944_3way Round 1 PASS): 멀티바이트 안전 cut — Python codepoint slice (mode_c_log.sh v2 동일 패턴)
  desc=$(grep -m1 'description:' "$skill_md" 2>/dev/null | sed 's/.*description:[[:space:]]*>*[[:space:]]*//' | sed 's/"//g' | "${PY_CMD:-python}" -c "import sys; data=sys.stdin.buffer.read().decode('utf-8',errors='replace'); sys.stdout.buffer.write(data.strip()[:60].encode('utf-8'))" 2>/dev/null)
  [ -z "$grade" ] && grade="-"
  [ -z "$desc" ] && desc="-"
  SKILL_ROWS="${SKILL_ROWS}| ${name} | ${grade} | ${desc} |
"
  SKILL_COUNT=$((SKILL_COUNT + 1))
done

SKILLS_BLOCK="### Skills (90_공통기준/스킬/) — ${SKILL_COUNT}개 등록

> 이 섹션은 \`generate_agents_guide.sh\`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스킬 | Grade | 설명 |
|------|-------|------|
${SKILL_ROWS}"

# --- AGENTS_GUIDE.md 마커 블록 치환 ---
TMP_FILE=$(mktemp)

IN_HOOKS=0
IN_SKILLS=0
HOOKS_WRITTEN=0
SKILLS_WRITTEN=0

while IFS= read -r line; do
  if echo "$line" | grep -q '<!-- AUTO_HOOKS_START -->'; then
    echo "$line" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
    echo "$HOOKS_BLOCK" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
    IN_HOOKS=1
    HOOKS_WRITTEN=1
    continue
  fi
  if echo "$line" | grep -q '<!-- AUTO_HOOKS_END -->'; then
    IN_HOOKS=0
    echo "$line" >> "$TMP_FILE"
    continue
  fi
  if echo "$line" | grep -q '<!-- AUTO_SKILLS_START -->'; then
    echo "$line" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
    echo "$SKILLS_BLOCK" >> "$TMP_FILE"
    echo "" >> "$TMP_FILE"
    IN_SKILLS=1
    SKILLS_WRITTEN=1
    continue
  fi
  if echo "$line" | grep -q '<!-- AUTO_SKILLS_END -->'; then
    IN_SKILLS=0
    echo "$line" >> "$TMP_FILE"
    continue
  fi
  if [ "$IN_HOOKS" -eq 0 ] && [ "$IN_SKILLS" -eq 0 ]; then
    echo "$line" >> "$TMP_FILE"
  fi
done < "$GUIDE"

if [ "$HOOKS_WRITTEN" -eq 0 ]; then
  echo "[WARN] <!-- AUTO_HOOKS_START --> 마커 미발견. AGENTS_GUIDE.md에 마커 블록을 추가하세요."
fi
if [ "$SKILLS_WRITTEN" -eq 0 ]; then
  echo "[WARN] <!-- AUTO_SKILLS_START --> 마커 미발견. AGENTS_GUIDE.md에 마커 블록을 추가하세요."
fi

cp "$TMP_FILE" "$GUIDE"
rm -f "$TMP_FILE"

echo "[OK] AGENTS_GUIDE.md 갱신 완료 — hooks ${HOOK_COUNT}개, skills ${SKILL_COUNT}개"
