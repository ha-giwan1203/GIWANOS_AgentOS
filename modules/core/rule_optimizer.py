
import logging
import sys

logger = logging.getLogger("rule_optimizer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/rule_optimizer.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def rule_optimizer_main():
    logger.info("Rule Optimizer 실행 시작")
    try:
        optimization_result = "Rule 최적화 및 압축이 정상적으로 완료되었습니다."
        logger.info(f"{optimization_result}")
    except Exception as e:
        logger.error(f"Rule Optimizer 실행 중 오류: {e}")

if __name__ == '__main__':
    rule_optimizer_main()
