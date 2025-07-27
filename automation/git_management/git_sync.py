# C:/giwanos/automation/git_management/git_sync.py

import os
from datetime import datetime
import git

def main():
    """
    GitHub 동기화를 수행합니다.
    변경사항이 없을 경우 예외를 무시합니다.
    """
    repo_path = os.path.abspath("C:/giwanos")
    repo = git.Repo(repo_path)
    # 스테이징
    repo.git.add("--all")
    # 커밋 메시지
    commit_message = f"Auto-sync on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        repo.git.commit("--no-verify", "-m", commit_message)
    except git.exc.GitCommandError as e:
        msg = str(e)
        if "nothing to commit" in msg.lower():
            print("[git_sync] No changes to commit.")
        else:
            raise
    # 푸시
    try:
        origin = repo.remote(name="origin")
        origin.push()
        print("[git_sync] Pushed to origin.")
    except Exception as e:
        print(f"[git_sync] Push failed: {e}")
        raise
