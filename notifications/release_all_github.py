import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import subprocess
import datetime

def run(cmd):
    print(f"💻 {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = "v" + datetime.datetime.now().strftime("%Y%m%d%H%M")
    message = f"🧠 GIWANOS 전체 릴리즈: {tag} - 루프 + 실행기 + 보고서 포함"

    with open("release_dummy.txt", "w", encoding="utf-8") as f:
        f.write(f"Release marker: {now}\n")

    run("git add .")
    run(f'git commit -m "{message}"')
    run("git pull --rebase --autostash")
    run("git push origin main")
    run(f"git tag {tag}")
    run(f"git push origin {tag}")

    print(f"✅ 전체 릴리즈 성공: {tag}")

if __name__ == "__main__":
    main()
