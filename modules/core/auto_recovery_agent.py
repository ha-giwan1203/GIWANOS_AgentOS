
import logging
import sys
import os

logger = logging.getLogger("auto_recovery_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/auto_recovery.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def main():
    logger.info("자동 복구 루틴 실행")
    flag_path = "C:/giwanos/data/logs/fault_flag.tmp"
    try:
        recovery_needed = os.path.exists(flag_path)
        if recovery_needed:
            logger.info("⚠️ 장애 플래그 발견. 복구 작업 수행 중...")
            os.remove(flag_path)
            logger.info("✅ 장애 복구 작업 완료. 플래그 제거 완료.")
        else:
            logger.info("✅ 장애 플래그 미발견. 복구 작업이 필요 없습니다.")
    except Exception as e:
        logger.error(f"자동 복구 루틴 실행 중 오류: {e}")

if __name__ == '__main__':
    main()
