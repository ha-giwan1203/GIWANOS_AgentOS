#!/bin/bash
# PreToolUse hook — 도메인 CLAUDE.md 미로드 시 도구 실행 차단 (화이트리스트 방식)
# 정책: domain_guard_config.yaml (단일 기준)
# v2: 도메인 활성 + loaded 미완 시 Read(대상 CLAUDE.md)만 허용, 나머지 전부 차단

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python으로 YAML 파싱 + 활성 도메인 확인 + 화이트리스트 차단 판정
RESULT=$(python3 -c "
import yaml, re, sys, json, os

config_path = sys.argv[1]
hook_input = sys.argv[2]

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

try:
    data = json.loads(hook_input)
except:
    sys.exit(0)

tool_name = data.get('tool_name', '')
tool_input = data.get('tool_input', {})

domains = cfg.get('domains', {})

for name, d in domains.items():
    flag_prefix = d.get('flag_prefix', '')
    active_flag = flag_prefix + '_active'
    loaded_flag = flag_prefix + '_loaded'

    # 이 도메인이 활성 상태인지 확인
    if not os.path.isfile(active_flag):
        continue

    # CLAUDE.md 이미 로드했으면 통과
    if os.path.isfile(loaded_flag):
        continue

    # === 화이트리스트 방식: Read(대상 CLAUDE.md)만 허용 ===
    claude_path = d.get('claude_path', '')

    # Read tool이고 대상이 도메인 CLAUDE.md이면 허용
    if tool_name == 'Read':
        file_path = tool_input.get('file_path', '').replace('\\\\', '/')
        if claude_path and claude_path.replace('\\\\', '/') in file_path:
            # 도메인 문서 읽기 — 허용
            sys.exit(0)

    # 그 외 모든 도구 차단
    reason = (
        f'[도메인 가드] {name} 도메인 활성 상태입니다. '
        f'먼저 {claude_path}를 Read tool로 읽으세요. '
        f'도메인 문서를 읽기 전에는 다른 도구를 사용할 수 없습니다.'
    )
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(0)

# 활성 도메인 없음 — 통과
sys.exit(0)
" "$CONFIG" "$INPUT" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
