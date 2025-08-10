
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
from datetime import datetime
import os
import time
import json

# 폴더별 정책
POLICIES = {
    "C:/giwanos/data/reports": {"retention_days": 30, "extensions": [".pdf", ".md", ".html", ".txt"]},
    "C:/giwanos/data/logs": {"retention_days": 60, "extensions": [".json", ".log", ".txt"]},
    "C:/giwanos/data/reflections": {"retention_days": 90, "extensions": [".json"]},
}

LOG_PATH = "C:/giwanos/data/logs/report_cleanup_log.json"

def cleanup_by_policy():
    now = time.time()
    deleted_total = []

    for folder, policy in POLICIES.items():
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            if any(fname.endswith(ext) for ext in policy["extensions"]):
                fpath = os.path.join(folder, fname)
                mtime = os.path.getmtime(fpath)
                age_days = (now - mtime) / 86400
                if age_days > policy["retention_days"]:
                    os.remove(fpath)
                    deleted_total.append({
                        "filename": fname,
                        "path": fpath,
                        "deleted_at": now_utc().isoformat(),
                        "age_days": round(age_days),
                        "folder": folder
                    })

    if deleted_total:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except json.JSONDecodeError:
                logs = []
        else:
            logs = []

        logs.extend(deleted_total)
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        print(f"🧹 {len(deleted_total)}개 파일 삭제됨. 로그 저장 완료.")
    else:
        print("✅ 삭제할 파일이 없습니다.")

if __name__ == "__main__":
    cleanup_by_policy()



