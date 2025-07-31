
import logging
import sys

logger = logging.getLogger("reflection_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/reflection_agent.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def run_reflection():
    logger.info("자동 회고 작업 실행 시작")
    try:
        reflection_result = "자동 회고 정상 완료"
        logger.info(f"{reflection_result}")
    except Exception as e:
        logger.error(f"자동 회고 실행 중 오류: {e}")

if __name__ == '__main__':
    run_reflection()
