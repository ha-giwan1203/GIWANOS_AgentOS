import os
from datetime import datetime
import logging

def generate_adaptive_reflection_report():
    base_dir = "C:/giwanos"
    reflections_dir = os.path.join(base_dir, "data/reflections")
    report_dir = os.path.join(base_dir, "data/reports")
    os.makedirs(report_dir, exist_ok=True)

    logger = logging.getLogger("adaptive_reflection_report")
    if not logger.handlers:
        logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/adaptive_reflection_report.log'))
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)

    recent_reflection_files = sorted(os.listdir(reflections_dir))[-3:]
    report_path = os.path.join(report_dir, f"adaptive_reflection_{datetime.now().strftime('%Y%m%d')}.md")

    report_content = f"# 🔍 자동 회고 보고서\n\n"
    report_content += f"**보고서 생성 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_content += "## 최근 자동 회고 내용:\n\n"

    for reflection_file in recent_reflection_files:
        filepath = os.path.join(reflections_dir, reflection_file)
        with open(filepath, 'r', encoding='utf-8') as file:
            reflection_content = file.read().strip()

        report_content += f"""
### [{reflection_file}]

{reflection_content}\n
"""

    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(report_content.strip())

    logger.info(f"✅ 자동 회고 보고서가 생성되었습니다: {report_path}")
    return report_path

if __name__ == '__main__':
    generate_adaptive_reflection_report()
