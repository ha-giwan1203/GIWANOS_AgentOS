# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변.
import os, sys, json, time
ROOT = "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

from modules.core.memory_adapter import MemoryAdapter
from modules.core.context_builder import build_context_block

HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")

def read_json(p):
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def main():
    m = MemoryAdapter()
    # 테스트용 한 줄 기록
    m.append_jsonl({
        "from": "user",
        "insight": "[boot-test] 새 방에서 맥락 복구 동작 확인",
        "raw": {"note": "context_boot"},
        "tags": ["명령","기억_유지","pipeline","test"]
    })

    block = build_context_block(limit=10, hours=48, required_tags=["명령","기억_유지"])
    print("=== CONTEXT BLOCK ===")
    print(block)
    print("=====================")

    h = read_json(HEALTH)
    ok = h.get("context_build_last_ok") and h.get("context_build_last_count", 0) >= 1
    print(f"PASS={bool(ok)}")

if __name__ == "__main__":
    main()
