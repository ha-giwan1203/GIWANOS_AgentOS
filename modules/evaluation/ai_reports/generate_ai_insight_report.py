
import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

EVALUATION_SCORE_PATH = "C:/giwanos/memory/loop_evaluation_score.json"
INSIGHT_REPORT_PATH = "C:/giwanos/data/reports/ai_insights.json"

def load_evaluation_data():
    try:
        with open(EVALUATION_SCORE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"평가 데이터 로드 실패: {e}")
        return {}

def generate_insights(evaluation_data):
    insights = []
    for key, value in evaluation_data.items():
        if isinstance(value, (int, float)):
            if value >= 90:
                insight = f"{key} 성능이 매우 우수합니다 ({value}점)."
            elif 70 <= value < 90:
                insight = f"{key} 성능이 양호하지만 개선 가능성이 있습니다 ({value}점)."
            else:
                insight = f"{key} 성능이 낮으며 즉각적인 개선이 필요합니다 ({value}점)."
            insights.append({"metric": key, "insight": insight, "score": value})
    return insights

def save_insights(insights):
    report = {
        "generated_at": datetime.now().isoformat(),
        "insights": insights
    }
    os.makedirs(os.path.dirname(INSIGHT_REPORT_PATH), exist_ok=True)
    with open(INSIGHT_REPORT_PATH, 'w', encoding='utf-8') as file:
        json.dump(report, file, indent=4, ensure_ascii=False)
    logging.info("[성공] AI 인사이트 보고서 저장 완료")

def main():
    evaluation_data = load_evaluation_data()
    insights = generate_insights(evaluation_data)
    save_insights(insights)

if __name__ == "__main__":
    main()
