import json
import os
from datetime import datetime
import logging

def generate_recovery_log_report():
    base_dir = "C:/giwanos"
    log_dir = os.path.join(base_dir, "data/logs")
    report_dir = os.path.join(base_dir, "data/reports")
    os.makedirs(report_dir, exist_ok=True)

    logger = logging.getLogger("recovery_log_report")
    if not logger.handlers:
        logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/recovery_log_report.log'))
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

    recovery_log_path = os.path.join(log_dir, "recovery_log.json")
    report_path = os.path.join(report_dir, f"recovery_log_{datetime.now().strftime('%Y%m%d')}.md")

    if not os.path.exists(recovery_log_path):
        logger.error("복구 이력 파일이 존재하지 않습니다.")
        return False

    with open(recovery_log_path, 'r', encoding='utf-8') as file:
        recovery_logs = json.load(file)

    report_content = f"# 🚨 장애 복구 이력 보고서\n\n"
    report_content += f"**보고서 생성 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_content += "## 최근 장애 복구 이력:\n\n"

    for idx, log in enumerate(recovery_logs[-5:], 1):
        report_content += f"""
### {idx}. 장애 복구 이력

- **발생 시각**: {log.get('timestamp', '정보 없음')}
- **상태**: {log.get('status', '정보 없음')}
- **상세 내용**: {log.get('details', '정보 없음')}\n
"""

    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(report_content.strip())

    logger.info(f"✅ 장애 복구 이력 보고서가 생성되었습니다: {report_path}")
    return report_path

if __name__ == '__main__':
    generate_recovery_log_report()


