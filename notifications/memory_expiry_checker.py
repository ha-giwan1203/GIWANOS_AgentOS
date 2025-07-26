import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime, timedelta

EXPIRY_DAYS = 14

def check_expired():
    with open("memory_timeline.json", "r", encoding="utf-8") as f:
        timeline = json.load(f)
    expired = []
    for item in timeline:
        timestamp = datetime.fromisoformat(item["timestamp"])
        if datetime.now() - timestamp > timedelta(days=EXPIRY_DAYS):
            expired.append(item)
    return expired

if __name__ == "__main__":
    expired = check_expired()
    if expired:
        print(f"⚠️ {len(expired)}개의 오래된 기억이 감지되었습니다:")
        for m in expired:
            print(f"[{m['timestamp']}] {m['content']}")
    else:
        print("✅ 모든 기억은 최신 상태입니다.")