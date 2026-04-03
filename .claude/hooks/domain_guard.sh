#!/bin/bash
# PreToolUse hook — 도메인 CLAUDE.md 미로드 시 도구 실행 차단 (화이트리스트 방식)
# 정책: domain_guard_config.yaml (단일 기준)
# v3: phase-based sequence guard (토론모드 3단: entry_read → doc_read → full)

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
INPUT=$(cat)
hook_log "PreToolUse" "domain_guard 발화"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/domain_guard_config.yaml"

if [ ! -f "$CONFIG" ]; then
  exit 0
fi

# Python으로 YAML 파싱 + 활성 도메인 확인 + phase-based 차단 판정
# v3.1: stdin 파이프 방식 (bash 변수 경유 제거 — cp949 인코딩 깨짐 방지)
RESULT=$(echo "$INPUT" | PYTHONIOENCODING=utf-8 python3 -c "
import yaml, re, sys, json, os

config_path = sys.argv[1]

# stdin에서 직접 JSON 읽기 (bash 변수 경유 없음)
try:
    raw = sys.stdin.buffer.read()
    data = json.loads(raw.decode('utf-8'))
except:
    sys.exit(0)

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

tool_name = data.get('tool_name', '')
tool_input = data.get('tool_input', {})

domains = cfg.get('domains', {})

for name, d in domains.items():
    flag_prefix = d.get('flag_prefix', '')
    active_flag = flag_prefix + '_active'
    loaded_flag = flag_prefix + '_loaded'
    entry_loaded_flag = flag_prefix + '_entry_loaded'
    phase_flag = flag_prefix + '_phase'

    # 이 도메인이 활성 상태인지 확인
    if not os.path.isfile(active_flag):
        continue

    phases = d.get('phases', [])
    claude_path = d.get('claude_path', '')
    entry_path = d.get('entry_path', '')

    # === phase-based guard (phases 정의가 있는 도메인만) ===
    if phases:
        # 현재 phase 판정
        current_phase = 'entry_read'  # 기본: 최초 단계
        if os.path.isfile(phase_flag):
            with open(phase_flag, 'r') as f:
                current_phase = f.read().strip() or 'entry_read'

        # phase 정의 찾기
        phase_def = None
        for p in phases:
            if p.get('name') == current_phase:
                phase_def = p
                break

        if not phase_def:
            # phase 정의 없으면 기본 차단
            phase_def = phases[0] if phases else {'allow_tools': ['Read'], 'allow_paths': []}

        allowed_tools = phase_def.get('allow_tools', [])
        allowed_paths = phase_def.get('allow_paths', [])

        # full phase이면 전부 허용
        if '*' in allowed_tools:
            sys.exit(0)

        # 도구 허용 체크
        tool_allowed = tool_name in allowed_tools

        if tool_allowed:
            # 경로 제한이 있으면 추가 체크
            if allowed_paths and tool_name == 'Read':
                file_path = tool_input.get('file_path', '').replace('\\\\', '/')
                path_ok = any(p in file_path for p in allowed_paths)
                # entry_read phase에서 ENTRY.md 또는 CLAUDE.md 읽기 허용
                if claude_path and claude_path.replace('\\\\', '/') in file_path:
                    path_ok = True
                if not path_ok:
                    reason = (
                        f'[도메인 가드 phase:{current_phase}] {name} 도메인 — '
                        f'현재 단계에서는 도메인 문서만 읽을 수 있습니다.'
                    )
                    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
                    sys.exit(0)
            sys.exit(0)  # 허용

        # 차단
        phase_desc = phase_def.get('description', current_phase)
        if current_phase == 'entry_read':
            target = entry_path or claude_path
            reason = (
                f'[도메인 가드 phase:entry_read] {name} 도메인 활성. '
                f'먼저 {target}를 Read tool로 읽으세요. '
                f'ENTRY.md → CLAUDE.md 순서로 읽어야 다음 단계로 진행됩니다.'
            )
        elif current_phase == 'doc_read':
            reason = (
                f'[도메인 가드 phase:doc_read] {name} 도메인 — '
                f'ENTRY.md는 읽었습니다. 이제 {claude_path}를 Read tool로 읽으세요. '
                f'도메인 문서를 읽어야 전체 도구가 해제됩니다.'
            )
        else:
            reason = (
                f'[도메인 가드 phase:{current_phase}] {name} 도메인 — '
                f'{phase_desc}. 허용 도구: {", ".join(allowed_tools)}'
            )
        print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
        sys.exit(0)

    # === 기존 방식 (phases 없는 도메인) ===
    # CLAUDE.md 이미 로드했으면 통과
    if os.path.isfile(loaded_flag):
        continue

    # Read tool이고 대상이 도메인 CLAUDE.md이면 허용
    if tool_name == 'Read':
        file_path = tool_input.get('file_path', '').replace('\\\\', '/')
        if claude_path and claude_path.replace('\\\\', '/') in file_path:
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
" "$CONFIG" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
