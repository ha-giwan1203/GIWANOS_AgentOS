
import os
import shutil
import subprocess

def run_command(cmd, shell=False):
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[❌] 명령 실패: {e}")
    except Exception as e:
        print(f"[⚠️] 예외 발생: {e}")

def backup_and_reinit_git():
    print("📦 기존 .git 폴더 백업 중...")
    if os.path.exists(".git"):
        try:
            os.rename(".git", ".git_broken_backup")
            print("✅ .git → .git_broken_backup 으로 백업 완료")
        except Exception as e:
            print(f"[❌] .git 폴더 백업 실패: {e}")
            return

    print("🧱 새로운 Git 리포지터리 초기화 중...")
    run_command(["git", "init"])

    if os.path.exists(".gitignore"):
        run_command(["git", "add", ".gitignore"])

    print("📂 전체 파일 추가 중...")
    run_command(["git", "add", "."])

    print("✅ 초기 커밋 생성 중...")
    run_command(["git", "commit", "-m", "🎯 Git 초기화 및 복구 완료"])

    print("☁️ Git 리포지터리 초기화 완료! 원격 저장소는 수동으로 설정해주세요.")

if __name__ == "__main__":
    print("🚀 Git 리포지터리 복구 스크립트 시작")
    backup_and_reinit_git()
    print("✅ 전체 완료")
