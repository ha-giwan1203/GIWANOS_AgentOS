
import os

def write_summary_text(system_status, reflection, report_dir, date_str):
    summary_path = f"{report_dir}/weekly_summary_{date_str}.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("📊 시스템 상태 로그\n")
        f.write(system_status + "\n\n")
        f.write("🧠 최신 리플렉션 요약\n")
        f.write(reflection + "\n")
