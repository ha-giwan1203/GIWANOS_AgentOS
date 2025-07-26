import logging
import os
from core.controller import Controller

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger('master_loop_logger')
logger.setLevel(logging.INFO)

# 파일 로그 핸들러 설정
file_handler = logging.FileHandler(os.path.join(log_dir, 'master_loop_execution.log'), encoding='utf-8')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 콘솔 로그 핸들러 추가 설정
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def main():
    logger.info("[시작] GIWANOS Master 루프 실행 시작")
    controller = Controller()
    controller.run()
    controller.run()
    # 📊 시스템 상태 진단 루프 실행
    try:
        from evaluation.insight.system_insight_agent import run_system_insight_loop
        logger.info("[중간] 시스템 상태 진단 시작")
        run_system_insight_loop()
        logger.info("[중간] 시스템 상태 진단 완료")
    except Exception as e:
        logger.warning(f"[오류] 시스템 진단 실패: {e}")

    logger.info("[완료] GIWANOS Master 루프 실행 완료")

if __name__ == "__main__":
    main()