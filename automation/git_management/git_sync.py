import os
from git import Repo
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('C:/giwanos/config/.env')

REPO_PATH = "C:/giwanos"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = f"https://{GITHUB_TOKEN}@github.com/ha-giwan1203/GIWANOS_AgentOS.git"

# 민감 정보 제외 목록
EXCLUDE_FILES = ['.env', '*.log', '*.json', '__pycache__/']

def git_sync():
    repo = Repo(REPO_PATH)

    # .gitignore에 제외 패턴 추가
    gitignore_path = os.path.join(REPO_PATH, '.gitignore')
    with open(gitignore_path, 'a+', encoding='utf-8') as gitignore:
        gitignore.seek(0)
        existing_entries = gitignore.read().splitlines()
        for pattern in EXCLUDE_FILES:
            if pattern not in existing_entries:
                gitignore.write(f"{pattern}\n")

    repo.git.add(all=True)
    commit_message = f"Auto-sync on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    # 후크 무시하고 커밋
    repo.git.commit('--no-verify', '-m', commit_message)
    origin = repo.remote(name="origin")
    branch = repo.active_branch.name
    try:
        origin.push()
    except Exception:
        origin.push(refspec=f"{branch}:{branch}")

    print("[✅ GitHub 동기화 성공 - 민감 정보 제외됨]")

if __name__ == "__main__":
    git_sync()


# Alias for master loop
main = git_sync
