# git_sync.py
import os
import sys
import subprocess
from pathlib import Path
from fnmatch import fnmatch

# ===== 설정 =====
REPO_DIR = Path(os.getenv("VELOS_REPO_DIR", r"C:\giwanos")).resolve()

# 자동 제외 패턴
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

# 동작 플래그 (환경 변수)
GIT_AUTOCOMMIT = os.getenv("GIT_AUTOCOMMIT", "1") != "0"
GIT_AUTOPUSH   = os.getenv("GIT_AUTOPUSH", "1") != "0"
GIT_FORCE_PUSH = os.getenv("GIT_FORCE_PUSH", "0") == "1"

# 출력 미리보기 개수 & 명령줄 길이 안전 임계값(보수적으로)
PREVIEW_MAX = 10
CMDLINE_MAX = 7000


# ===== 유틸 =====
def env_prefix() -> str:
    # 로그에 보일 환경 변수 프리픽스 (실행에는 영향 없음; 실행엔 하단 run()의 env가 사용됨)
    return f"GIT_AUTOCOMMIT={'1' if GIT_AUTOCOMMIT else '0'} " \
           f"GIT_AUTOPUSH={'1' if GIT_AUTOPUSH else '0'} " \
           f"GIT_FORCE_PUSH={'1' if GIT_FORCE_PUSH else '0'}"

def run(cmd, cwd=REPO_DIR, check=True, capture=False):
    # 실행 시 현재 중요한 env를 같이 보여줌
    print(f"[git_sync] 실행: {env_prefix()} :: {' '.join(cmd)} (cwd={cwd})")
    env = os.environ.copy()  # 하위 프로세스에 동일 env 전달
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
        env=env,
    )

def norm(p: str) -> str:
    return p.replace("\\", "/")

def is_excluded(path_str: str) -> bool:
    p = norm(path_str)
    for pat in EXCLUDE_PATTERNS:
        pat_n = norm(pat)

        # 디렉터리 패턴 "xxx/" 가 경로에 포함되면 제외
        if pat_n.endswith("/") and pat_n in p:
            return True

        # 글롭 매칭(** 포함)
        if fnmatch(p, pat_n):
            return True

        # 완전 동일
        if p == pat_n:
            return True
    return False

def get_current_branch() -> str:
    try:
        r = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True, capture=True)
        return r.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"


# ===== 메인 =====
def main():
    if not REPO_DIR.exists():
        print(f"[git_sync] ❌ repo 경로 없음: {REPO_DIR}")
        sys.exit(1)
    if not (REPO_DIR / ".git").exists():
        print(f"[git_sync] ❌ .git 폴더가 없습니다: {REPO_DIR}")
        sys.exit(1)

    os.chdir(REPO_DIR)

    if not GIT_AUTOCOMMIT:
        print("[git_sync] ⚠ 자동 커밋 비활성화(GIT_AUTOCOMMIT=0)")
        return

    # 변경 파일 수집
    try:
        status = run(["git", "status", "--porcelain"], check=True, capture=True)
    except subprocess.CalledProcessError:
        print("[git_sync] ❌ git status 실패")
        return

    raw_lines = [ln for ln in status.stdout.splitlines() if ln.strip()]
    if not raw_lines:
        print("[git_sync] ℹ 변경된 파일 없음")
        return

    changed_files = []
    for line in raw_lines:
        # 보통 'XY path' 형태. 공백 뒤가 경로
        path = line[3:] if len(line) > 3 else line.strip()
        # rename일 경우 'old -> new' → new만 취함
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        # 제외 규칙 적용
        if not is_excluded(path):
            changed_files.append(path)

    if not changed_files:
        print("[git_sync] ℹ 변경된 파일은 있으나, 모두 제외 패턴에 해당")
        return

    # 변경 파일 미리보기(콘솔 도배 방지)
    total = len(changed_files)
    if total > PREVIEW_MAX:
        print(f"[git_sync] 변경 파일 {total}개 (첫 {PREVIEW_MAX}개만 표시):")
        for f in changed_files[:PREVIEW_MAX]:
            print("   -", f)
    else:
        print(f"[git_sync] 변경 파일 {total}개:")
        for f in changed_files:
            print("   -", f)

    # 스테이징: 너무 길면 자동으로 '.' 사용
    add_cmd = ["git", "add"] + changed_files
    if len(" ".join(add_cmd)) > CMDLINE_MAX or total > 2000:
        # 파일이 아주 많으면 직접 나열하지 말고 전체 추가
        print("[git_sync] ℹ 파일이 많아 'git add .' 로 대체")
        add_cmd = ["git", "add", "."]

    try:
        run(add_cmd, check=True)
    except subprocess.CalledProcessError:
        print("[git_sync] ❌ git add 실패")
        return

    # 커밋
    try:
        run(["git", "commit", "-m", "🔁 자동 커밋: 최신 파일 자동 백업"], check=True)
    except subprocess.CalledProcessError:
        print("[git_sync] ❌ 커밋 실패 (변경사항 없음 또는 훅 에러)")
        return

    if not GIT_AUTOPUSH:
        print("[git_sync] ⚠ 자동 푸시 비활성화(GIT_AUTOPUSH=0)")
        return

    # 푸시
    branch = get_current_branch()
    push_cmd = ["git", "push", "origin", branch]
    if GIT_FORCE_PUSH:
        push_cmd.append("--force")

    try:
        run(push_cmd, check=True)
        print("[git_sync] ✅ 푸시 완료")
    except subprocess.CalledProcessError:
        print("[git_sync] ❌ 푸시 실패")


# 외부에서 import 시 사용할 엔트리
def sync_with_github():
    main()


if __name__ == "__main__":
    main()
