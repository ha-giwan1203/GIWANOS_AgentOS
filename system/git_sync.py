# C:/giwanos/git_sync.py

import os
import subprocess
from datetime import datetime

def log_summary(msg):
    log_file = os.path.join(os.getcwd(), 'logs', f'git_sync_{datetime.now():%Y%m%d}.log')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%H:%M:%S} {msg}\n')
    print(msg)  # 화면에는 한 줄만

def run_git_push():
    try:
        result = subprocess.run(
            ['git', 'push'],
            capture_output=True, text=True, check=True
        )
        log_summary("✅ git push 성공 (업스트림 정상)")
    except subprocess.CalledProcessError as e:
        # 업스트림 없음 에러 메시지 대응
        if "set-upstream" in e.stderr or "no upstream" in e.stderr or "have no upstream" in e.stderr:
            subprocess.run(
                ['git', 'branch', '--set-upstream-to=origin/main'],
                capture_output=True, text=True
            )
            try:
                subprocess.run(['git', 'push'], capture_output=True, text=True, check=True)
                log_summary("✅ git push 성공 (업스트림 자동 복구)")
            except Exception as e2:
                log_summary("❌ git push 실패 (업스트림 복구 실패)")
        else:
            log_summary(f"❌ git push 실패: {str(e.stderr).strip().splitlines()[-1]}")
    except Exception as ex:
        log_summary(f"❌ git_sync 예외: {str(ex)}")

if __name__ == "__main__":
    run_git_push()
