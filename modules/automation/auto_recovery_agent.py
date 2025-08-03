
import psutil
import subprocess
import logging
import time

class AutoRecoveryAgent:
    def __init__(self, check_interval=10, max_retries=3):
        self.check_interval = check_interval
        self.max_retries = max_retries
        self.logger = logging.getLogger("auto_recovery_agent")
        self.logger.setLevel(logging.INFO)

    def perform_auto_recovery(self):
        retries = 0
        while retries < self.max_retries:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if 'python' in proc.info['name']:
                        continue  # python 프로세스는 제외 (예시)

                    if not proc.is_running():
                        self.logger.warning(f"{proc.info['name']} 비정상 종료 감지, 재시작 시도 중...")
                        proc.terminate()
                        subprocess.Popen(proc.info['cmdline'])
                        self.logger.info(f"{proc.info['name']} 재시작 성공")
                        
                return

            except Exception as e:
                self.logger.error(f"재시작 실패: {e}")
                retries += 1
                time.sleep(2 ** retries)  # 지수 백오프 (Exponential Back-off)

        self.logger.critical("자동 복구 최대 재시도 초과, 수동 개입 필요")
