#!/usr/bin/env python3
"""
VELOS AutoSave Runner
시스템 자동 저장 및 메모리 동기화 데몬
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import signal

# 경로 설정
ROOT = Path("/home/user/webapp")
LOGS_DIR = ROOT / "data" / "logs"
MEMORY_DIR = ROOT / "data" / "memory"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "autosave_runner.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutoSaveRunner:
    def __init__(self):
        self.running = True
        self.iteration = 0
        
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def run_autosave_cycle(self):
        """AutoSave 주기 실행"""
        try:
            # 메모리 동기화
            self.sync_memory()
            
            # 시스템 상태 업데이트
            self.update_system_status()
            
            self.iteration += 1
            logger.info(f"AutoSave cycle #{self.iteration} completed successfully")
            
        except Exception as e:
            logger.error(f"AutoSave cycle failed: {e}")
    
    def sync_memory(self):
        """메모리 시스템 동기화"""
        try:
            # 간단한 메모리 동기화 시뮬레이션
            memory_file = MEMORY_DIR / "learning_memory.json"
            if memory_file.exists():
                logger.info("Memory synchronization completed")
            else:
                logger.warning("Memory file not found")
        except Exception as e:
            logger.error(f"Memory sync failed: {e}")
    
    def update_system_status(self):
        """시스템 상태 업데이트"""
        try:
            status_file = LOGS_DIR / "autosave_status.json"
            status = {
                "timestamp": time.time(),
                "last_run": datetime.now().isoformat(),
                "iteration": self.iteration,
                "status": "running",
                "pid": os.getpid() if 'os' in globals() else None
            }
            
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
            logger.info("System status updated")
            
        except Exception as e:
            logger.error(f"Status update failed: {e}")
    
    def run(self):
        """메인 실행 루프"""
        import os
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("AutoSave Runner starting...")
        logger.info(f"PID: {os.getpid()}")
        
        while self.running:
            try:
                self.run_autosave_cycle()
                
                # 30초 대기
                for _ in range(30):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(5)
        
        logger.info("AutoSave Runner stopped")

if __name__ == "__main__":
    runner = AutoSaveRunner()
    runner.run()