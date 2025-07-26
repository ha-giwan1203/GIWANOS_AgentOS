import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime, timedelta

def check_for_retirement():
    with open("loop_experience_log.json", "r", encoding="utf-8") as f:
        log = json.load(f)

    now = datetime.now()
    retired = {}

    for loop, data in log.items():
        total = data.get("successes", 0) + data.get("failures", 0)
        if total == 0:
            continue
        failure_rate = data.get("failures", 0) / total
        last = data.get("last_run", "2000-01-01T00:00:00")
        last_run = datetime.fromisoformat(last)
        days_since = (now - last_run).days

        if failure_rate >= 0.8 or days_since > 30:
            retired[loop] = {
                "retired_at": now.isoformat(),
                "reason": f"실패율 {failure_rate:.2f}, {days_since}일 이상 미사용"
            }

    with open("loop_retirement_log.json", "w", encoding="utf-8") as f:
        json.dump(retired, f, indent=2, ensure_ascii=False)

    print(f"✅ 폐기 대상 루프 수: {len(retired)}")

if __name__ == "__main__":
    check_for_retirement()
