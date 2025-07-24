
import os
import subprocess
from datetime import datetime

BASE_DIR = "C:/giwanos"
LOG_DIR = os.path.join(BASE_DIR, 'logs')

def log_summary(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f'git_sync_{datetime.now():%Y%m%d}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%H:%M:%S} {msg}\n')
    print(msg)

def run_git_push():
    try:
        subprocess.run(['git', '-C', BASE_DIR, 'add', 'logs/'], check=True)
        subprocess.run(['git', '-C', BASE_DIR, 'add', 'reports/'], check=True)
        subprocess.run(['git', '-C', BASE_DIR, 'add', 'docs/'], check=True)
        subprocess.run('git -C "{}" add *.md'.format(BASE_DIR), shell=True, check=True)
        subprocess.run('git -C "{}" add system/*.py'.format(BASE_DIR), shell=True, check=True)

        subprocess.run(['git', '-C', BASE_DIR, 'commit', '-m', f'Auto commit {datetime.now():%Y-%m-%d %H:%M:%S}'], check=True)
        subprocess.run(['git', '-C', BASE_DIR, 'push'], check=True)

        log_summary("✅ git push 성공 (자동화 완료)")
    except subprocess.CalledProcessError as e:
        log_summary(f"❌ git push 실패: {e.stderr if e.stderr else e.stdout}")
    except Exception as ex:
        log_summary(f"❌ git_sync 예외: {str(ex)}")

if __name__ == "__main__":
    run_git_push()
