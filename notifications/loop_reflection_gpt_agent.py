import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime
import os

def load_template(loop_name, template_file="loop_reflection_templates.json"):
    if os.path.exists(template_file):
        with open(template_file, "r", encoding="utf-8") as f:
            templates = json.load(f)
        return templates.get(loop_name, templates.get("default", "루프 실행 완료."))
    return "루프 실행 완료."

def reflect_loop(loop_name, success=True):
    comment = load_template(loop_name)
    now = datetime.now().isoformat()

    log = {}
    try:
        with open("loop_reflection_live_log.json", "r", encoding="utf-8") as f:
            log = json.load(f)
    except:
        pass

    log[loop_name] = {
        "executed_at": now,
        "gpt_comment": comment
    }

    with open("loop_reflection_live_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    md = f"## 루프: {loop_name}\n"
    md += f"✅ 실행 시각: {now}\n"
    md += f"🧠 GPT 회고: {comment}\n"

    with open("loop_reflection_live_report.md", "a", encoding="utf-8") as f:
        f.write(md + "\n\n")

    print(f"🧠 회고 완료: {loop_name}")

if __name__ == "__main__":
    reflect_loop("loop_reflection", success=True)
