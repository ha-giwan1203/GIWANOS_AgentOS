import os
import sys
import subprocess
from pathlib import Path
from fnmatch import fnmatch

# ===== 설정 =====
REPO_DIR = Path(os.getenv("VELOS_REPO_DIR", r"C:\giwanos")).resolve()

# 환경 변수 스위치
GIT_AUTOCOMMIT  = os.getenv("GIT_AUTOCOMMIT", "1") != "0"
GIT_AUTOPUSH    = os.getenv("GIT_AUTOPUSH", "1") != "0"
GIT_FORCE_PUSH  = os.getenv("GIT_FORCE_PUSH", "0") == "1"
GIT_NO_VERIFY   = os.getenv("GIT_NO_VERIFY", "0") == "1"
GIT_SYNC_VERBOSE = os.getenv("GIT_SYNC_VERBOSE", "0") == "1"  # 1이면 상세 로그

# 제외 패턴 (디렉터리/글롭 혼용)
EXCLUDE_PATTERNS = [
    # 민감/환경
    "configs/.env", "*.env", "*.env.local", "*.env.*",

    # 대용량/빌드 산출물
    ".patch_backups/", "node_modules/", "interface/**/node_modules/",

    # 로그/캐시/임시
    "data/logs/", "**/*.log", "**/*.log.*", "**/*.cache", "**/*.tmp", "**/*.temp", "**/*.swp",

    # DB류
    "**/*.sqlite", "**/*.db",

    # 리포트 산출물
    "data/reports/*.pdf", "data/reports/*.pptx",

    # 기타 백업 파일
    "**/*.bak",
]

def _log(msg: str):
    # 기본은 조용히. VERBOSE=1이면 자세히 출력
    if GIT_SYNC_VERBOSE:
        print(msg)

def _print(msg: str):
    # 항상 보여줄 핵심 메시지
    print(msg)

def run(cmd, cwd=REPO_DIR, check=True, capture=False):
    # 실행 커맨드는 VERBOSE에서만 보임
    _log(f"[git_sync] 실행: {' '.join(cmd)} (cwd={cwd})")
    return subprocess.run(
        cmd, cwd=cwd, check=check,
        capture_output=capture, text=True
    )

def norm(p: str) -> str:
    return p.replace("\\", "/")

def is_excluded(path_str: str) -> bool:
    p = norm(path_str)
    for pat in EXCLUDE_PATTERNS:
        pat_n = norm(pat)
        # 디렉터리 패턴: "xxx/" 가 경로에 포함되면 제외
        if pat_n.endswith("/") and pat_n in p:
            return True
        # 글롭 매칭(** 포함)
        if fnmatch(p, pat_n):
            return True
        # 정확히 동일
        if p == pat_n:
            return True
    return False

def get_current_branch() -> str:
    try:
        r = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True, capture=True)
        return r.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"

def collect_changed_files():
    try:
        status = run(["git", "status", "--porcelain"], check=True, capture=True)
    except subprocess.CalledProcessError:
        _print("[git_sync] ❌ git status 실패")
        return []

    changed_files = []
    for line in status.stdout.splitlines():
        if not line.strip():
            continue
        # 'XY path' 형태. 공백 뒤가 경로
        path = line[3:] if len(line) > 3 else line.strip()
        # rename: 'old -> new' → new만 사용
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if is_excluded(path):
            _log(f"[git_sync] 🚫 제외됨: {path}")
        else:
            changed_files.append(path)

    return changed_files

def stage_files(files):
    """파일 수가 많거나 경로가 길면 자동으로 'git add .'로 폴백."""
    if not files:
        return False

    # 윈도우 길이 제한 회피: 너무 많으면 그냥 전체 add
    use_bulk_add = len(files) > 200

    if use_bulk_add:
        _log("[git_sync] ℹ 파일이 많아 'git add .' 로 대체")
        try:
            run(["git", "add", "."])
            return True
        except subprocess.CalledProcessError:
            _print("[git_sync] ❌ git add . 실패")
            return False

    try:
        run(["git", "add"] + files)
        return True
    except FileNotFoundError as e:
        # WinError 206 (경로/명령 너무 김) 등
        _log(f"[git_sync] ⚠ 개별 add 실패({e}); 'git add .'로 폴백")
        try:
            run(["git", "add", "."])
            return True
        except subprocess.CalledProcessError:
            _print("[git_sync] ❌ git add . 실패")
            return False
    except subprocess.CalledProcessError:
        _print("[git_sync] ❌ git add 실패")
        return False

def commit_changes():
    commit_cmd = ["git", "commit", "-m", "🔁 자동 커밋: 최신 파일 자동 백업"]
    if GIT_NO_VERIFY:
        commit_cmd.append("--no-verify")

    try:
        run(commit_cmd)
        return True
    except subprocess.CalledProcessError:
        _print("[git_sync] ❌ 커밋 실패 (변경사항 없음 또는 훅 에러)")
        return False

def push_changes():
    branch = get_current_branch()
    push_cmd = ["git", "push", "origin", branch]
    if GIT_FORCE_PUSH:
        push_cmd.append("--force")

    try:
        run(push_cmd)
        _print("[git_sync] ✅ 푸시 완료")
        return True
    except subprocess.CalledProcessError:
        _print("[git_sync] ❌ 푸시 실패")
        return False

def main():
    if not REPO_DIR.exists():
        _print(f"[git_sync] ❌ repo 경로 없음: {REPO_DIR}")
        sys.exit(1)

    os.chdir(REPO_DIR)

    if not GIT_AUTOCOMMIT:
        _print("[git_sync] ⚠ 자동 커밋 비활성화(GIT_AUTOCOMMIT=0)")
        return

    changed_files = collect_changed_files()
    if not changed_files:
        _print("[git_sync] ℹ 변경된 파일 없음(혹은 전부 제외됨)")
        return

    # 간단 요약만 출력 (전체 목록은 VERBOSE에서만)
    _print(f"[git_sync] 변경 파일 {len(changed_files)}개 감지")
    if GIT_SYNC_VERBOSE:
        preview = "\n   - " + "\n   - ".join(changed_files[:10])
        _log(f"[git_sync] (미리보기 상위 10개){preview}")

    if not stage_files(changed_files):
        return

    if not commit_changes():
        return

    if not GIT_AUTOPUSH:
        _print("[git_sync] ⚠ 자동 푸시 비활성화(GIT_AUTOPUSH=0)")
        return

    push_changes()

# 마스터 루프에서 import해 호출할 함수
def git_sync():
    main()

if __name__ == "__main__":
    main()
