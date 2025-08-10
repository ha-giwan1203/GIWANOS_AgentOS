
import os

def export_to_markdown(system_status, reflection, report_dir, date_str):
    content = f"# 📊 VELOS 시스템 리포트 ({date_str})\n\n"
    content += f"## 시스템 상태 로그\n\n{system_status}\n\n"
    content += f"## 최신 리플렉션 요약\n\n{reflection}\n"
    with open(f"{report_dir}/weekly_summary_{date_str}.md", "w", encoding="utf-8") as f:
        f.write(content)

def export_to_html(system_status, reflection, report_dir, date_str):
    content = f"<html><body><h1>📊 VELOS 시스템 리포트 ({date_str})</h1>"
    content += f"<h2>시스템 상태 로그</h2><pre>{system_status}</pre>"
    content += f"<h2>최신 리플렉션 요약</h2><pre>{reflection}</pre>"
    content += "</body></html>"
    with open(f"{report_dir}/weekly_summary_{date_str}.html", "w", encoding="utf-8") as f:
        f.write(content)


