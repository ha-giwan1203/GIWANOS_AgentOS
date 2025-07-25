import subprocess

def git_sync():
    subprocess.run(['git', 'add', '.'], encoding='utf-8', errors='ignore')
    subprocess.run(['git', 'commit', '-m', '자동 동기화'], encoding='utf-8', errors='ignore')
    subprocess.run(['git', 'push', 'origin', 'HEAD:main'], encoding='utf-8', errors='ignore')
    print("[성공] GitHub 동기화 완료")

if __name__ == "__main__":
    git_sync()