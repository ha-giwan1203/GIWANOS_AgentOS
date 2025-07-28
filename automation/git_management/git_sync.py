
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

def main():
    try:
        subprocess.run(["git", "push", "--set-upstream", "origin", "giwanos-main"], cwd="C:/giwanos", check=True)
        logging.info("[✅ GitHub 동기화 성공]")
    except subprocess.CalledProcessError as e:
        logging.error(f"[❌ GitHub 동기화 실패] {e}")

if __name__ == "__main__":
    main()
