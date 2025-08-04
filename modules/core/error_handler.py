import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('C:/giwanos/data/logs/error_handler.log'),
        logging.StreamHandler()
    ]
)

def handle_exception(e, context=""):
    error_message = f"🚨 오류 발생 [{context}]: {str(e)}"
    detailed_traceback = traceback.format_exc()

    # 콘솔에 오류 즉시 출력
    print(error_message)
    print(detailed_traceback)

    # 로그에 오류 상세히 기록
    logging.error(error_message)
    logging.error(detailed_traceback)
