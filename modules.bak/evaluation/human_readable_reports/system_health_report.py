
import json
from datetime import datetime
import os

def generate_system_health_report():
    base_dir = "C:/giwanos"
    log_dir = os.path.join(base_dir, "data/logs")
    report_dir = os.path.join(base_dir, "data/reports")
    os.makedirs(report_dir, exist_ok=True)

    system_health_path = os.path.join(log_dir, "system_health.json")
    report_path = os.path.join(report_dir, f"system_health_{datetime.now().strftime('%Y%m%d')}.md")

    if not os.path.exists(system_health_path):
        return False

    with open(system_health_path, 'r', encoding='utf-8') as file:
        system_health = json.load(file)

    report_content = f"""
# 🖥️ 시스템 상태 보고서

**보고서 생성 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

| 항목                 | 값              |
|----------------------|-----------------|
| CPU 사용률           | {system_health.get('cpu_usage_percent', 'N/A')}% |
| 메모리 사용률        | {system_health.get('memory_usage_percent', 'N/A')}% |
| 디스크 사용률        | {system_health.get('disk_usage_percent', 'N/A')}% |
| 활성 프로세스 수     | {system_health.get('active_process_count', 'N/A')}개 |
"""

    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(report_content.strip())

    return report_path

if __name__ == '__main__':
    print(generate_system_health_report())


