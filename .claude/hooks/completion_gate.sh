#!/bin/bash
# completion-gate v2: Stop 이벤트 시 상태 문서 갱신 강제
# dirty marker 존재 시 TASKS.md/HANDOFF.md가 dirty 이후 수정됐는지 확인
# 미갱신이면 Stop 차단 → Claude가 자동 갱신 후 재시도
# GPT+Claude 합의 2026-04-02
source "$(dirname "$0")/hook_common.sh" 2>/dev/null
hook_log "Stop" "completion_gate 발화"

# Python 내부에서 경로 구성 (한국어 경로 bash→python 인코딩 문제 방지)
RESULT=$(PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -c "
import os, sys, json
from datetime import datetime
from pathlib import Path

# 프로젝트 디렉토리 탐색
project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
root = Path(project_dir)

dirty_flag = root / '90_공통기준' / 'agent-control' / 'state' / 'dirty.flag'
tasks = root / '90_공통기준' / '업무관리' / 'TASKS.md'
handoff = root / '90_공통기준' / '업무관리' / 'HANDOFF.md'
status = root / '90_공통기준' / '업무관리' / 'STATUS.md'

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
    msg = f'[COMPLETION GATE] 작업 파일 변경 후 상태 문서 미갱신: {\", \".join(missing)}{status_warn} — 갱신 후 다시 종료하세요.'
    print(json.dumps({'decision': 'block', 'reason': msg}, ensure_ascii=False))
else:
    # TASKS/HANDOFF 갱신됨 — STATUS만 경고 (차단 아님)
    if status_warn:
        print(json.dumps({'message': f'[COMPLETION GATE] TASKS/HANDOFF 갱신 확인.{status_warn}'}, ensure_ascii=False))
    # dirty marker 삭제
    try:
        dirty_flag.unlink()
    except:
        pass

    # finish_state.json 체크 (GPT 합의 2026-04-04)
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
                    msg = f'[COMPLETION GATE] finish 루틴 미완료: {", ".join(pending_steps)} — /finish 8단계를 완료하세요.'
                    print(json.dumps({'decision': 'block', 'reason': msg}, ensure_ascii=False))
        except:
            pass
" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
