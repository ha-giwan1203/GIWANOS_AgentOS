
import os
import subprocess

def remove_index_lock():
    lock_file = os.path.join(".git", "index.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("[🧹] .git/index.lock 제거 완료")
        except Exception as e:
            print(f"[⚠️] index.lock 제거 실패: {e}")

def remove_git_cached_files():
    # 주로 제외해야 할 경로들 (상황 맞게 추가 가능)
    ignore_targets = [
        ".tmp.driveupload", "__pycache__", "*.log", "*.md", "*.pdf", "*.DS_Store"
    ]
    for pattern in ignore_targets:
        try:
            subprocess.run(["git", "rm", "-r", "--cached", pattern], check=True)
            print(f"[✅] Git 캐시 제거 완료: {pattern}")
        except subprocess.CalledProcessError:
            print(f"[⚠️] 캐시 제거 실패 또는 추적 없음: {pattern}")

def run_git_gc():
    try:
        subprocess.run(["git", "gc", "--prune=now"], check=True)
        print("[🧹] Git 최적화 완료 (gc + prune)")
    except Exception as e:
        print(f"[⚠️] git gc 실패: {e}")

if __name__ == "__main__":
    print("🚀 Git 캐시 정리 루틴 시작")
    remove_index_lock()
    remove_git_cached_files()
    run_git_gc()
    print("✅ Git 정리 루프 완료")
