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

# TASKS/HANDOFF 언급 파일 예외: 상태 문서에 경로가 명시된 파일은 의도적 산출물
def get_mentioned_files():
    mentioned = set()
    for doc_name in ['TASKS.md', 'HANDOFF.md']:
        doc_path = root / '90_공통기준' / '업무관리' / doc_name
        if doc_path.exists():
            try:
                content = doc_path.read_text(encoding='utf-8')
                for u in untracked:
                    # 파일명이 문서에 언급되어 있으면 예외
                    fname = Path(u).name
                    if fname in content:
                        mentioned.add(u)
            except Exception:
                pass
    return mentioned

# 도메인 산출물 예외: 도메인 폴더 내 신규 파일은 작업 산출물로 간주
DOMAIN_PREFIXES = [
    '05_생산실적/',
    '10_라인배치/',
    '04_생산계획/',
    '90_공통기준/스킬/',
    '90_공통기준/토론모드/',
    '_플랜/',
]

def is_domain_output(rel_path):
    for dp in DOMAIN_PREFIXES:
        if rel_path.startswith(dp):
            # 도메인 폴더 내 .py/.md/.xlsx/.json은 산출물로 간주
            ext = Path(rel_path).suffix.lower()
            if ext in ('.py', '.md', '.xlsx', '.json', '.yaml', '.yml', '.sh', '.bat'):
                return True
    return False

mentioned_files = get_mentioned_files()
cleanup_candidates = [
    f for f in untracked
    if not is_exempt(f) and f not in mentioned_files and not is_domain_output(f)
]

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
