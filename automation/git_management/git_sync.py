# C:/giwanos/automation/git_management/git_sync.py

import os
from datetime import datetime
import git

def main():
    """
    GitHub 동기화를 수행합니다.
    - 변경사항이 없으면 무시
    - 최초 푸시 시 upstream 브랜치 설정
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
        if "nothing to commit" in str(e).lower():
            print("[git_sync] No changes to commit.")
        else:
            print(f"[git_sync] Commit failed: {e}")
            return

    origin = repo.remote(name="origin")
    try:
        origin.push()
        print("[git_sync] Pushed to origin.")
    except git.exc.GitCommandError as e:
        msg = str(e)
        if "has no upstream branch" in msg.lower():
            branch = repo.active_branch.name
            print(f"[git_sync] No upstream for branch '{branch}', setting upstream and pushing.")
            try:
                origin.push('--set-upstream', 'origin', branch)
                print("[git_sync] Push with upstream set succeeded.")
            except Exception as e2:
                print(f"[git_sync] Push with upstream failed: {e2}")
        else:
            print(f"[git_sync] Push failed: {e}")
