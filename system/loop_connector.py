import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import subprocess
import json
from pathlib import Path
from datetime import datetime

base = Path(__file__).resolve().parent
memory_file = base / "loop_memory_state.json"
log_file = base / "loop_result_log.json"

def load_state():
    if not memory_file.exists():
        print("❌ 기억 상태 파일 누락")
        return {}
    return json.loads(memory_file.read_text(encoding="utf-8"))

def update_memory(field):
    state = load_state()
    state[field] = True
    memory_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def log_result(loop_name, status, note=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {"loop": loop_name, "status": status, "timestamp": timestamp, "note": note}
    if log_file.exists():
        data = json.loads(log_file.read_text(encoding="utf-8"))
    else:
        data = {"results": []}
    data["results"].append(result)
    log_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def git_commit_push(commit_msg):
    try:
        subprocess.run(["git", "add", "."], cwd=base, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=base, check=True)
        subprocess.run(["git", "push"], cwd=base, check=True)
        print("✅ GitHub push 완료")
    except Exception as e:
        print("⚠️ GitHub push 실패:", e)

def conditional_run(description, condition, script, memory_key, git_note):
    print(f"🔎 {description}")
    if condition:
        try:
            print(f"➡️ 실행: {script}")
            subprocess.run(["python", str(base / script)], check=True)
            update_memory(memory_key)
            log_result(script, "pass")
            git_commit_push(git_note)
        except Exception as e:
            print(f"❌ 실패: {e}")
            log_result(script, "fail", str(e))
    else:
        print(f"⏭️ 조건 미충족 → {script} 생략")

def main():
    state = load_state()
    conditional_run(
        "Slack 전송 여부 판단",
        state.get("reflection_log_created") and not state.get("slack_posted"),
        "send_slack_report.py", "slack_posted", "Slack 전송 성공"
    )
    conditional_run(
        "Notion 업로드 여부 판단",
        state.get("reflection_log_created") and not state.get("notion_uploaded"),
        "upload_notion_safe.py", "notion_uploaded", "Notion 업로드 성공"
    )
    conditional_run(
        "ZIP 백업 여부 판단",
        not state.get("zip_backup_done"),
        "zip_backup_generator.py", "zip_backup_done", "ZIP 백업 성공"
    )

if __name__ == "__main__":
    main()
