#!/bin/bash
# PostToolUse(Read) hook — 도메인 문서 로드 완료 플래그 + phase 전환 관리
# 정책: domain_guard_config.yaml (단일 기준)
# v2: ENTRY.md → phase:doc_read, CLAUDE.md → phase:full 전환

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python으로 YAML 파싱 + 읽은 파일 경로 매칭 + phase 전환
python3 -c "
import yaml, sys, json, os

config_path = sys.argv[1]
hook_input = sys.argv[2]

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

try:
    data = json.loads(hook_input)
except:
    sys.exit(0)

tool_input = data.get('tool_input', {})
file_path = tool_input.get('file_path', '')

if not file_path:
    sys.exit(0)

# 경로 구분자 통일 (Windows backslash → forward slash)
file_path_normalized = file_path.replace('\\\\', '/')

domains = cfg.get('domains', {})

for name, d in domains.items():
    claude_path = d.get('claude_path', '')
    entry_path = d.get('entry_path', '')
    flag_prefix = d.get('flag_prefix', '')
    active_flag = flag_prefix + '_active'
    loaded_flag = flag_prefix + '_loaded'
    phase_flag = flag_prefix + '_phase'
    phases = d.get('phases', [])

    # 활성 도메인만 대상
    if not os.path.isfile(active_flag):
        continue

    # === phase-based 도메인 ===
    if phases:
        # ENTRY.md 읽기 → phase:doc_read 전환
        if entry_path and entry_path.replace('\\\\', '/') in file_path_normalized:
            with open(phase_flag, 'w') as f:
                f.write('doc_read')
            break

        # CLAUDE.md 읽기 → phase:full 전환 + loaded 플래그
        if claude_path and claude_path.replace('\\\\', '/') in file_path_normalized:
            with open(phase_flag, 'w') as f:
                f.write('full')
            open(loaded_flag, 'w').close()
            break

    else:
        # === 기존 방식 (phases 없는 도메인) ===
        if claude_path and claude_path.replace('\\\\', '/') in file_path_normalized:
            open(loaded_flag, 'w').close()
            break
" "$CONFIG" "$INPUT" 2>/dev/null

exit 0
