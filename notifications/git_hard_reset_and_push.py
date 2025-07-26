
import os
import shutil
import subprocess

def run(cmd, shell=False):
    print(f"💻 {cmd}")
    subprocess.run(cmd, shell=shell, check=True)

def hard_reset_git():
    print("🧨 기존 .git 폴더 완전 삭제 중...")
    if os.path.exists(".git"):
        shutil.rmtree(".git")
        print("✅ .git 삭제 완료")

    print("🧱 새로운 Git 리포지터리 초기화...")
    run(["git", "init"])

    print("📄 .gitignore 다시 반영")
    if os.path.exists(".gitignore"):
        run(["git", "add", ".gitignore"])

    print("📂 전체 파일 추가 중...")
    run(["git", "add", "."])

    print("✅ 첫 커밋 생성 중...")
    run(["git", "commit", "-m", "🎯 클린 Git 재시작"])

    print("🔗 원격 저장소 연결")
    run(["git", "remote", "add", "origin",
     "https://github.com/ha-giwan1203/GIWANOS_AgentOS.git"])
         
    print("☁️ GitHub로 강제 push")
    run(["git", "push", "-u", "origin", "main", "--force"])

if __name__ == "__main__":
    print("🚀 Git 완전 초기화 스크립트 시작")
    hard_reset_git()
    print("✅ 모든 Git 재설정 완료")
