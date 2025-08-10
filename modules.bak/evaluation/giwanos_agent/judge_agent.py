# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import json
import logging

logger = logging.getLogger(__name__)

class JudgeAgent:
    def __init__(self):
        self.analysis_path = "C:/giwanos/data/logs/api_cost_log.json"

    def load_latest_analysis(self):
        try:
            with open(self.analysis_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and "analysis_result" in data[-1]:
                    return data[-1]["analysis_result"]
                return "No valid analysis result found"
        except Exception as e:
            logger.error(f"Error loading analysis result: {e}")
            return "No analysis data available"

    def run_loop(self):
        logger.info("JudgeAgent 루프 실행 시작")
        analysis = self.load_latest_analysis()
        if "장애" in analysis or "경고" in analysis:
            self.trigger_alert(analysis)
        else:
            logger.info("JudgeAgent: 시스템 정상 상태 유지 중.")
        logger.info("JudgeAgent 루프 정상 완료")

    def trigger_alert(self, analysis):
        logger.warning(f"JudgeAgent 경고 발생 → {analysis}")


# ✅ 외부에서 호출할 수 있도록 전역 함수 래퍼 추가
def run_judge_loop():
    agent = JudgeAgent()
    agent.run_loop()


