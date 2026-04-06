#!/bin/bash
# completion-gate v3: Stop 이벤트 통합 완료 게이트
# pre_finish_guard(verify.json) + completion_gate(TASKS/HANDOFF) 통합
# GPT+Claude 토론 합의 2026-04-06
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "completion_gate 발화"

RESULT=$(PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -c "
import os, sys, json, re
from datetime import datetime
from pathlib import Path

project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
root = Path(project_dir)

state_dir = root / '90_공통기준' / 'agent-control' / 'state'
dirty_flag = state_dir / 'dirty.flag'
current_task_file = state_dir / 'current_task'
tasks = root / '90_공통기준' / '업무관리' / 'TASKS.md'
handoff = root / '90_공통기준' / '업무관리' / 'HANDOFF.md'
status = root / '90_공통기준' / '업무관리' / 'STATUS.md'

def block(reason):
    print(json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False))
    sys.exit(0)

# === 1. finish_state.json 체크 (dirty.flag와 독립) ===
finish_state_path = state_dir / 'finish_state.json'
if finish_state_path.exists():
    try:
        fs = json.loads(finish_state_path.read_text(encoding='utf-8'))
        ts = fs.get('terminal_state', '')
        if ts not in ('done', 'exception', ''):
            pending_steps = []
            if not fs.get('committed_pushed'): pending_steps.append('커밋+푸시')
            if not fs.get('gpt_shared'): pending_steps.append('GPT 공유')
            if not fs.get('gpt_judgment'): pending_steps.append('GPT 판정 확인')
            if not fs.get('user_reported'): pending_steps.append('사용자 보고')
            if not fs.get('followup_checked'): pending_steps.append('후속 확인')
            if pending_steps:
                block(f'[COMPLETION GATE] finish 루틴 미완료: {\", \".join(pending_steps)} — /finish 8단계를 완료하세요.')
    except:
        pass

# === 2. verify.json 체크 (구 pre_finish_guard 로직) ===
if current_task_file.exists():
    raw = current_task_file.read_text(encoding='utf-8').strip()
    if raw:
        task_dir = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        plan_path = task_dir / 'plan.md'
        if plan_path.exists() and dirty_flag.exists():
            plan_text = plan_path.read_text(encoding='utf-8')
            if re.search(r'^\s*verify_required\s*:\s*true\s*$', plan_text, re.I | re.M):
                verify_path = task_dir / 'verify.json'
                if not verify_path.exists():
                    block('verify.json 이 없습니다. verifier를 실행하고 PASS 결과를 만든 뒤 완료 보고하세요.')
                try:
                    v = json.loads(verify_path.read_text(encoding='utf-8'))
                    if str(v.get('status', '')).lower().strip() != 'pass':
                        block('verify.json status=pass 가 아닙니다.')
                    if verify_path.stat().st_mtime < dirty_flag.stat().st_mtime:
                        block('verify.json 이 최신 변경보다 오래되었습니다. 재검증하세요.')
                except json.JSONDecodeError:
                    block('verify.json 파싱 실패.')

# === 3. TASKS/HANDOFF 갱신 체크 ===
if not dirty_flag.exists():
    sys.exit(0)

dirty_ts_str = dirty_flag.read_text(encoding='utf-8').strip().split('\n')[0]
if not dirty_ts_str:
    sys.exit(0)

try:
    dirty_ts = datetime.strptime(dirty_ts_str, '%Y-%m-%d %H:%M:%S')
except:
    sys.exit(0)

missing = []
for name, path in [('TASKS.md', tasks), ('HANDOFF.md', handoff)]:
    if not path.exists():
        missing.append(name)
        continue
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    if mtime < dirty_ts:
        missing.append(name)

status_warn = ''
if status.exists():
    st_mtime = datetime.fromtimestamp(status.stat().st_mtime)
    if st_mtime < dirty_ts:
        status_warn = ' (참고: STATUS.md도 미갱신)'

if missing:
    block(f'[COMPLETION GATE] 작업 파일 변경 후 상태 문서 미갱신: {\", \".join(missing)}{status_warn} — 갱신 후 다시 종료하세요.')
else:
    if status_warn:
        print(json.dumps({'message': f'[COMPLETION GATE] TASKS/HANDOFF 갱신 확인.{status_warn}'}, ensure_ascii=False))
    try:
        dirty_flag.unlink()
    except:
        pass

" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
