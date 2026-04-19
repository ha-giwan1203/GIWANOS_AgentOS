#!/bin/bash
# PreToolUse(Bash) advisory hook — permissions 1회용 패턴 + 완전 중복 자동 탐지
# 의제5 3자 토론 합의(2026-04-19 debate_20260418_190429_3way) Phase 2-A 산출물
# 등급: advisory (exit 0 강제, stderr 경고만, 차단 없음)
#
# 탐지 대상:
#  - 1회용: PID echo, URL echo, 특정 파일 rm/rmdir, state 파일 rm, 드리프트 sed
#  - 완전 동일 중복 항목
#
# 성능: 매 Bash 호출마다 실행되므로 60분 캐시로 재검사 스킵

set -u
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
# 훅 등급: advisory (Phase 2-A 신설, Phase 2-C timing 배선)
_PS_START=$(hook_timing_start)

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"
SETTINGS_TEAM="$PROJECT_ROOT/.claude/settings.json"
SETTINGS_LOCAL="$PROJECT_ROOT/.claude/settings.local.json"
CACHE_FILE="$PROJECT_ROOT/.claude/state/permissions_sanity_last.txt"
CACHE_TTL=3600  # 60분

# 캐시 확인 (advisory이므로 너무 자주 실행하지 않음)
if [ -f "$CACHE_FILE" ]; then
  last_ts=$(cat "$CACHE_FILE" 2>/dev/null || echo 0)
  now=$(date +%s 2>/dev/null || echo 0)
  elapsed=$((now - last_ts))
  if [ "$elapsed" -lt "$CACHE_TTL" ] 2>/dev/null; then
    hook_timing_end "permissions_sanity" "$_PS_START" "skip_cache"
    exit 0
  fi
fi

# JSON 파싱 + 탐지 (Python 1회 실행)
if [ ! -f "$SETTINGS_TEAM" ] && [ ! -f "$SETTINGS_LOCAL" ]; then
  hook_timing_end "permissions_sanity" "$_PS_START" "skip_nosettings"
  exit 0
fi

WARNINGS=$(PYTHONUTF8=1 python3 - <<'PYEOF' 2>/dev/null
import json, re, sys
from collections import Counter
from pathlib import Path

# 세션74: team+local union으로 1회용/중복 탐지
allow = []
for p in (Path('.claude/settings.json'), Path('.claude/settings.local.json')):
    if not p.exists():
        continue
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    allow.extend(d.get('permissions', {}).get('allow', []))

patterns = [
    (re.compile(r'^Bash\(echo ["\']\d{10,}["\']\)$'), 'PID echo 하드코딩'),
    (re.compile(r'^Bash\(echo ["\']https?://.*["\']\)$'), 'URL echo 하드코딩'),
    (re.compile(r'^Bash\(rm -f "C:.+"\)$'), '특정 파일 rm'),
    (re.compile(r'^Bash\(rmdir "C:.+"\)$'), '특정 디렉토리 rmdir'),
    (re.compile(r'^Bash\(rm -f \.claude/state/.+\)$'), 'state 파일 rm'),
    (re.compile(r'^Bash\(sed -i .+\)$'), '1회성 sed'),
]

oneoff = []
for item in allow:
    for pat, label in patterns:
        if pat.match(item):
            oneoff.append((label, item))
            break

c = Counter(allow)
dups = [(k, v) for k, v in c.items() if v > 1]

if oneoff or dups:
    if oneoff:
        print(f"[permissions_sanity] 1회용 항목 {len(oneoff)}건 감지:")
        for label, item in oneoff[:5]:
            print(f"  [{label}] {item[:100]}")
        if len(oneoff) > 5:
            print(f"  ... 외 {len(oneoff) - 5}건")
    if dups:
        print(f"[permissions_sanity] 완전 중복 {len(dups)}건 감지:")
        for k, v in dups:
            print(f"  {k} (x{v})")
    print("[permissions_sanity] 조치: 포괄 패턴(Bash(echo:*)) 이미 있으면 1회용 재등록은 중복. settings.local.json 직접 정리 권장.")
PYEOF
)

if [ -n "$WARNINGS" ]; then
  echo "$WARNINGS" >&2
  hook_log "PreToolUse/Bash" "permissions_sanity 경고: $(echo "$WARNINGS" | head -1)" 2>/dev/null || true
  _ps_status="warn"
else
  _ps_status="clean"
fi

# 캐시 갱신
mkdir -p "$(dirname "$CACHE_FILE")" 2>/dev/null || true
date +%s > "$CACHE_FILE" 2>/dev/null || true

hook_timing_end "permissions_sanity" "$_PS_START" "$_ps_status"
exit 0
