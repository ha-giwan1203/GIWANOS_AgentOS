
import logging
import sys

# 로거 명시적 설정
logger = logging.getLogger("cot_evaluator")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/cot_evaluator.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def evaluate_cot():
    logger.info("CoT 평가 실행 시작")
    try:
        # 실제 평가 로직 구현 전 예시
        score = 95.2  # 예시 평가 점수
        ranking = 1   # 예시 순위
        logger.info(f"CoT 평가 결과 - 점수: {score}, 순위: {ranking}")
    except Exception as e:
        logger.error(f"CoT 평가 중 오류 발생: {e}")

# 직접 실행 시에도 실행 가능하도록 유지
if __name__ == '__main__':
    evaluate_cot()


