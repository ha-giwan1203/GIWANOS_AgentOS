import subprocess

def git_sync():
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', '자동 동기화'])
    subprocess.run(['git', 'push', 'origin', 'HEAD:main'])
    print("[성공] GitHub 동기화 완료")

if __name__ == "__main__":
    git_sync()