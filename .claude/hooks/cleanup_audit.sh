#!/bin/bash
# cleanup_audit.sh: Stop 시 untracked 비무시 파일 감지 → 정리 권고 → 미정리 시 차단
# GPT+Claude 합의 2026-04-02
# - completion_gate와 분리 (기능별 독립)
# - 자동 삭제 금지, 98_아카이브/정리대기_YYYYMMDD/ 이동 권고
# - 예외: .claude/, .gitignore 대상, TASKS/HANDOFF 언급 파일

RESULT=$(PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -c "
import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime

project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
root = Path(project_dir)

# git status --porcelain: ?? = untracked
try:
    out = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True, cwd=str(root), encoding='utf-8'
    )
    lines = out.stdout.strip().split('\n') if out.stdout.strip() else []
except Exception:
    sys.exit(0)

untracked = []
for line in lines:
    if not line.startswith('?? '):
        continue
    fpath = line[3:].strip().strip('\"')
    untracked.append(fpath)

if not untracked:
    sys.exit(0)

# 예외 패턴
EXEMPT_PREFIXES = [
    '.claude/',
    '90_공통기준/agent-control/',
    '98_아카이브/',
]

EXEMPT_SUFFIXES = [
    'CLAUDE.md',
    'TASKS.md',
    'HANDOFF.md',
    'STATUS.md',
    'README.md',
    '.gitignore',
]

def is_exempt(rel_path):
    for prefix in EXEMPT_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    for suffix in EXEMPT_SUFFIXES:
        if rel_path.endswith(suffix):
            return True
    # .skill 파일은 의도적 산출물
    if rel_path.endswith('.skill'):
        return True
    return False

cleanup_candidates = [f for f in untracked if not is_exempt(f)]

if not cleanup_candidates:
    sys.exit(0)

today = datetime.now().strftime('%Y%m%d')
archive_dir = f'98_아카이브/정리대기_{today}'
file_list = ', '.join(cleanup_candidates[:10])
suffix = f' 외 {len(cleanup_candidates)-10}건' if len(cleanup_candidates) > 10 else ''

msg = (
    f'[CLEANUP AUDIT] untracked 파일 {len(cleanup_candidates)}건 발견: {file_list}{suffix}'
    f' — {archive_dir}/로 이동하거나 .gitignore에 추가한 뒤 다시 종료하세요.'
)
print(json.dumps({'decision': 'block', 'reason': msg}, ensure_ascii=False))
" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT"
fi

exit 0
