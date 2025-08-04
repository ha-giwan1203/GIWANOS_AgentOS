import json
import logging

logger = logging.getLogger(__name__)

class JudgeAgent:
    def __init__(self):
        self.analysis_path = "C:/giwanos/data/logs/api_cost_log.json"

    def load_latest_analysis(self):
        with open(self.analysis_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data[-1]["analysis_result"]

    def run_loop(self):
        logger.info("JudgeAgent 루프 실행 시작")
        analysis = self.load_latest_analysis()
        if "장애" in analysis or "경고" in analysis:
            self.trigger_alert(analysis)
        else:
            logger.info("JudgeAgent: 시스템 정상 상태 유지 중.")
        logger.info("JudgeAgent 루프 정상 완료")

    def trigger_alert(self, analysis):
        logger.warning(f"JudgeAgent: 즉각적인 주의 필요 → {analysis}")
