# [EXPERIMENT] scripts/check_ingest.py
from modules.core.memory_adapter.adapter import MemoryAdapter
import time
import os
import json
import sqlite3

adapter = MemoryAdapter()

# 완전히 새로운 테스트 입력 생성
unique_ts = int(time.time())
item = {
    "from": "test_user",
    "insight": f"unique ingest test at {unique_ts}",
    "tags": ["unique_test", "ingest_check"],
    "ts": unique_ts
}
adapter.append_jsonl(item)

print("[OK] JSONL append:", item)

# 플러시 테스트
print("\n=== Flush Test ===")
stats_before = adapter.get_stats()
print("Before flush:", stats_before)

# JSONL 파일 직접 확인
jsonl_path = "C:/giwanos/data/memory/learning_memory.jsonl"
print(f"\nJSONL file exists: {os.path.exists(jsonl_path)}")
if os.path.exists(jsonl_path):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"JSONL total lines: {len(lines)}")
        print(f"Last line: {lines[-1].strip() if lines else 'No lines'}")

# 수동 플러시 테스트
print("\n=== Manual Flush Test ===")
try:
    # JSONL에서 첫 번째 라인 읽기
    with open(jsonl_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        if first_line:
            print(f"First line: {first_line}")
            obj = json.loads(first_line)
            print(f"Parsed object: {obj}")
            
            # DB에 직접 삽입 시도
            db_path = "C:/giwanos/data/velos.db"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            
            # 스키마 확인
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
            if cur.fetchone():
                print("Memory table exists")
                
                # 삽입 시도
                cur.execute(
                    "INSERT INTO memory(ts, role, insight, raw, tags) VALUES (?, ?, ?, ?, ?)",
                    (
                        int(obj.get("ts", int(time.time()))),
                        str(obj.get("from") or obj.get("role") or "system"),
                        str(obj.get("insight", "")),
                        json.dumps(obj.get("raw", ""), ensure_ascii=False),
                        json.dumps(obj.get("tags", []), ensure_ascii=False),
                    ),
                )
                conn.commit()
                print("Manual insert successful")
            else:
                print("Memory table does not exist")
            
            conn.close()
        else:
            print("No lines in JSONL file")
except Exception as e:
    print(f"Manual flush error: {e}")

moved = adapter.flush_jsonl_to_db()
print(f"\nAdapter flush records: {moved}")

stats_after = adapter.get_stats()
print("After flush:", stats_after)

# 최근 레코드 확인
print("\n=== Recent Records ===")
recent = adapter.recent(limit=5)
for i, record in enumerate(recent):
    print(f"{i+1}. {record}")

# 검색 테스트
print("\n=== Search Test ===")
search_results = adapter.search("unique_test", limit=5)
print(f"Search results for 'unique_test': {len(search_results)} records")
for i, result in enumerate(search_results):
    print(f"{i+1}. {result}")

# 통계 확인
print("\n=== Final Stats ===")
final_stats = adapter.get_stats()
print(f"Buffer size: {final_stats['buffer_size']}")
print(f"DB records: {final_stats['db_records']}")
print(f"Last sync: {final_stats['last_sync']}")

print("\n=== Ingest Pipeline Test Complete ===")
