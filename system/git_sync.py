
import subprocess

def git_sync():
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "자동 커밋: GIWANOS 데이터 업데이트"])
    subprocess.run(["git", "push"])
    print("✅ GitHub 동기화 완료")

if __name__ == "__main__":
    git_sync()
