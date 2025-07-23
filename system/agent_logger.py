# agent_logger.py
import json
import os
import datetime

LOG_DIR = "agent_logs"
os.makedirs(LOG_DIR, exist_ok=True)

def save_agent_status(agent_name: str, status: str, extra: dict = None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = datetime.datetime.now().strftime("agent_log_%Y%m%d.json")
    path = os.path.join(LOG_DIR, filename)

    log_entry = {
        "agent": agent_name,
        "status": status,
        "timestamp": timestamp
    }

    if extra:
        log_entry.update(extra)

    # 기존 로그 불러오기
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(log_entry)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"📝 상태 저장됨: {path}")
