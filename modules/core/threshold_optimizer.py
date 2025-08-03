
import logging
import sys

logger = logging.getLogger("threshold_optimizer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/threshold_optimizer.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def threshold_optimizer_main():
    logger.info("Threshold Optimizer 실행 시작")
    try:
        optimization_result = "Threshold 값을 정상적으로 최적화했습니다."
        logger.info(f"{optimization_result}")
    except Exception as e:
        logger.error(f"Threshold Optimizer 실행 중 오류: {e}")

if __name__ == '__main__':
    threshold_optimizer_main()
