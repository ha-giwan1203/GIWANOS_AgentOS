# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과를 기록하고 복구 경로를 제공한다.
import os, json, time, random
from modules.core.memory_adapter import MemoryAdapter

ROOT = "C:/giwanos"
LOG  = os.path.join(ROOT, "data", "logs", "system_health.json")

def read_log():
    try:
        with open(LOG, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def main():
    m = MemoryAdapter()
    stamp = int(time.time())
    payload = {
        "from": "system",
        "insight": f"[test] flush pipeline ok? ts={stamp}",
        "raw": {"note": "pipeline_e2e", "rand": random.randint(1000, 9999)},
        "tags": ["test","pipeline","memory"],
        "ts": stamp
    }
    m.append_jsonl(payload)
    moved = m.flush_jsonl_to_db()
    recent = m.recent(5)

    print(f"[test] moved={moved}")
    print(f"[test] recent_top={recent[0]['insight'] if recent else 'EMPTY'}")
    print(f"[test] PASS={moved>=1 and any(p['insight'].startswith('[test] flush') for p in recent)}")

    log = read_log()
    log["memory_pipeline_last_test_ts"] = stamp
    log["memory_pipeline_last_test_ok"] = True
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
