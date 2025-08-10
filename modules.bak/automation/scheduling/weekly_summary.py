import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)

def generate_weekly_summary(report_dir):
    today = datetime.now().strftime('%Y%m%d')
    summary_path = Path(report_dir) / f'weekly_summary_{today}.md'
    summary_content = "# 주간 요약 보고서\n\n이번 주의 시스템 운영 및 성능 요약입니다."
    
    summary_path.write_text(summary_content, encoding='utf-8')
    logging.info(f'Weekly summary created: {summary_path}')
    
    return summary_path


