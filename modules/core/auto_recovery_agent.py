import logging
import json

logger = logging.getLogger("auto_recovery_agent")
logger.setLevel(logging.INFO)

def load_latest_analysis():
    with open('C:/giwanos/data/logs/api_cost_log.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data[-1]["analysis_result"]

def main():
    latest_analysis = load_latest_analysis()
    if "장애" in latest_analysis or "경고" in latest_analysis:
        logger.info("⚠️ 장애 분석 결과 발견. 복구 작업 수행 중...")
        perform_auto_recovery(latest_analysis)
        logger.info("✅ 자동 복구 작업 완료.")
    else:
        logger.info("✅ 장애 분석 결과 없음. 복구 작업 불필요.")

def perform_auto_recovery(issue):
    logger.info(f"자동 복구 시작: {issue}")
    # 실제 복구 로직 구현 (필요한 로직 추가)
