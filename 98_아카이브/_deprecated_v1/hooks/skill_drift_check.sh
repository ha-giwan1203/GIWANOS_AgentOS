#!/bin/bash
# PreToolUse(Bash) advisory hook — skill wrapper / 실물 SKILL.md 정합성 검증
# 의제3 Phase A (2026-04-19 세션71) — skill-creator 경로화 합의 이행
#   래퍼(.claude/commands/<name>.md)와 실물(90_공통기준/스킬/<name>/SKILL.md 등) 정합성
# 의제5 훅 등급: advisory (exit 0, stderr 경고만, 차단 없음)
# 성능: git commit 명령 감지 시에만 실행 (매 Bash 호출 전수 검사 회피)

set -u
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
# 훅 등급: advisory (Phase A 신설, Phase 2-C 2026-04-19 세션73 timing 배선)
_SDC_START=$(hook_timing_start)

INPUT=$(cat 2>/dev/null || echo '')
COMMAND=$(echo "$INPUT" | safe_json_get "command" 2>/dev/null || echo '')

# git commit 명령이 아니면 스킵 (advisory — 성능 보호)
if [ -z "$COMMAND" ] || ! echo "$COMMAND" | grep -qE '\bgit commit\b'; then
  hook_timing_end "skill_drift_check" "$_SDC_START" "skip_noncommit"
  exit 0
fi

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"
COMMANDS_DIR="$PROJECT_ROOT/.claude/commands"

if [ ! -d "$COMMANDS_DIR" ]; then
  hook_timing_end "skill_drift_check" "$_SDC_START" "skip_nodir"
  exit 0
fi

# 이관 대상 5종 매핑 (의제3 Phase A)
WARNINGS=$(PYTHONUTF8=1 "$PY_CMD" - <<'PYEOF' 2>/dev/null
import os, sys
from pathlib import Path

project_root = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.'))

# Phase A 대상 5종: wrapper_name → skill.md path
targets = {
    'debate-mode':            '90_공통기준/토론모드/debate-mode/SKILL.md',
    'settlement':             '90_공통기준/스킬/assembly-cost-settlement/SKILL.md',
    'line-batch-management':  '90_공통기준/스킬/line-batch-management/SKILL.md',
    'line-batch-outer-main':  '90_공통기준/스킬/line-batch-outer-main/SKILL.md',
    'daily':                  '90_공통기준/스킬/daily-routine/SKILL.md',
}

drifts = []
for name, skill_rel in targets.items():
    wrapper = project_root / '.claude' / 'commands' / f'{name}.md'
    skill = project_root / skill_rel
    if not wrapper.exists():
        drifts.append(f"[MISSING wrapper] .claude/commands/{name}.md")
        continue
    if not skill.exists():
        drifts.append(f"[MISSING skill] {skill_rel}")
        continue
    # 정합성 — description 키워드 교차 확인 (느슨한 매칭)
    try:
        wrap_txt = wrapper.read_text(encoding='utf-8', errors='ignore')
        skill_txt = skill.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        drifts.append(f"[READ FAIL] {name}: {e}")
        continue
    # 래퍼의 첫 헤딩과 실물이 서로의 이름을 포함하는지
    if name not in wrap_txt:
        drifts.append(f"[DRIFT] wrapper {name}.md does not reference its own name")
    if name not in skill_txt.lower() and name.replace('-', '_') not in skill_txt.lower():
        # 일부 실물은 다른 식별자를 사용할 수 있음. 경고만
        pass

if drifts:
    print("[skill_drift_check] 정합성 경고:")
    for d in drifts:
        print(f"  {d}")
    print("[skill_drift_check] 조치: 래퍼 또는 실물 SKILL.md 재생성 권장. 세션72에서 skill-creator 동기화 기능 확장 예정.")
PYEOF
)

if [ -n "$WARNINGS" ]; then
  echo "$WARNINGS" >&2
  hook_log "PreToolUse/Bash" "skill_drift_check 경고 (git commit 시점)" 2>/dev/null || true
  hook_timing_end "skill_drift_check" "$_SDC_START" "warn"
else
  hook_timing_end "skill_drift_check" "$_SDC_START" "clean"
fi

exit 0
