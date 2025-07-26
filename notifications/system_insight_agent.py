from datetime import datetime
import json
from reporting.generate_pdf_report import create_pdf_from_insights
from system.send_email import send_pdf_report

def get_system_improvement_questions():
    return [
        {"category": "자동화 오류/병목", "question": "현재 자동화된 프로세스에서 병목 현상이나 반복적 오류가 있는가?"},
        {"category": "배포 최적화", "question": "코드 배포 과정에서 발생하는 비효율적인 단계가 있는가?"},
        {"category": "알림 채널", "question": "추가적인 알림 채널이 필요한가?"},
        {"category": "모니터링", "question": "시스템 모니터링의 사각지대가 존재하는가?"},
        {"category": "UX / 데이터 접근", "question": "사용자의 데이터 접근과 검색 효율을 높일 방법이 있는가?"},
        {"category": "피드백 루프", "question": "피드백 수집 및 시스템 개선 주기가 충분히 효과적인가?"}
    ]

def evaluate_questions(questions):
    results = []
    for q in questions:
        result = {
            "category": q["category"],
            "question": q["question"],
            "issue": "점검 필요",
            "severity": "중간",
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
    return results

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_markdown(data, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# GIWANOS 시스템 상태 보고서\n\n")
        for item in data:
            f.write(f"- 🟠 **[{item['category']}]** {item['question']} → {item['issue']} (심각도: {item['severity']})\n")

def run_system_insight_loop():
    questions = get_system_improvement_questions()
    results = evaluate_questions(questions)
    save_json(results, "logs/system_health.json")
    save_markdown(results, "logs/system_health.md")
    pdf_path = create_pdf_from_insights("logs/system_health.json")
    send_pdf_report(pdf_path)
    return results
