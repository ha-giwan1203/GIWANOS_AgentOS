#!/bin/bash
# PostToolUse(Read) hook — 도메인 CLAUDE.md 로드 완료 플래그 관리
# 정책: domain_guard_config.yaml (단일 기준)

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python으로 YAML 파싱 + 읽은 파일 경로 매칭 + loaded 플래그 생성
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
    flag_prefix = d.get('flag_prefix', '')
    active_flag = flag_prefix + '_active'
    loaded_flag = flag_prefix + '_loaded'

    # 활성 도메인만 대상
    if not os.path.isfile(active_flag):
        continue

    # 읽은 파일이 도메인 CLAUDE.md인지 확인
    if claude_path and claude_path.replace('\\\\', '/') in file_path_normalized:
        open(loaded_flag, 'w').close()
        break
" "$CONFIG" "$INPUT" 2>/dev/null

exit 0
