import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import subprocess
import datetime
import json

ZIP_TARGET = "GIWANOS_FINAL_INSTALL_COMPLETE.zip"
TAG_PREFIX = "v"

def run_git(commands):
    for cmd in commands:
        print(f"💻 {cmd}")
        subprocess.run(cmd, shell=True, check=True)

def main():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version_tag = TAG_PREFIX + datetime.datetime.now().strftime("%Y%m%d%H%M")
    message = f"Release {version_tag} - Automated GIWANOS Release"

    # Dummy 커밋 유도
    with open("release_dummy.txt", "w", encoding="utf-8") as f:
        f.write(f"Release executed: {message}\n")

    run_git(["git add ."])
    run_git([f'git commit -m "{message} (자동 커밋)"'])

    # 🔁 변경 사항 임시 저장 → pull → 복원
    run_git(["git stash"])
    run_git(["git pull origin main --rebase"])
    run_git(["git stash pop"])

    # 최종 push 및 태그
    run_git([
        "git push origin main",
        f"git tag {version_tag}",
        f"git push origin {version_tag}"
    ])

    print(f"✅ Release pushed: {version_tag}")

if __name__ == "__main__":
    main()


