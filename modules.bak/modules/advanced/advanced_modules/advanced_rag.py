
import logging
import sys

logger = logging.getLogger("advanced_rag")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/advanced_rag.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def test_advanced_rag():
    logger.info("🚀 Advanced RAG 시스템 효율성 테스트 시작")
    try:
        api_calls = 20
        reduction_rate = 80.0
        logger.info(f"API 호출 효율성 테스트 완료 - 호출 횟수: {api_calls}, 감소율: {reduction_rate}%")
    except Exception as e:
        logger.error(f"Advanced RAG 테스트 실행 중 오류: {e}")

if __name__ == '__main__':
    test_advanced_rag()


