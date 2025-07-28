# auto_run_weekly_summary.py 최종 구성본
import sys
sys.path.append("C:/giwanos")

from scheduling.weekly_summary import generate_weekly_summary
import logging

logging.basicConfig(level=logging.INFO)

def auto_run():
    report_dir = "C:/giwanos/data/reports"
    generate_weekly_summary(report_dir)

if __name__ == "__main__":
    auto_run()
