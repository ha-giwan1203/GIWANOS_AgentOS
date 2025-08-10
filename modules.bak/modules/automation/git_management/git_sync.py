import subprocess
import logging
import os

logging.basicConfig(level=logging.INFO)

REPO_DIR = "C:/giwanos"

def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=REPO_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"[❌] 현재 브랜치 조회 실패: {e}")
        return "main"

def has_changes():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_DIR,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def main():
    branch = get_current_branch()

    if not has_changes():
        logging.info("[ℹ️] 변경된 파일이 없어 git 커밋/푸시 생략됨")
        return

    try:
        subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
        subprocess.run(
            ["git", "commit", "-m", "🔁 자동 커밋: 최신 파일 자동 백업"],
            cwd=REPO_DIR,
            check=True
        )
        subprocess.run(
            ["git", "push", "origin", branch, "--force"],
            cwd=REPO_DIR,
            check=True
        )
        logging.info("[✅ GitHub 자동 커밋 및 푸시 완료]")
    except subprocess.CalledProcessError as e:
        logging.error(f"[❌ GitHub 푸시 실패] {e}")

# ✅ 마스터 루프에서 호출 가능한 함수 이름
def sync_with_github():
    main()

if __name__ == "__main__":
    main()


