#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Memory Sync Check Script

메모리 동기화 상태를 확인하는 스크립트입니다.
"""

import os
import sys
import json
import time
from pathlib import Path

# ROOT 경로 설정
ROOT = Path("${VELOS_ROOT:-/workspace}")
if ROOT not in sys.path:
    sys.path.append(str(ROOT))


def check_memory_sync():
    """메모리 동기화 상태 확인"""
    print("=== VELOS Memory Sync Check ===")

    # 1. 메모리 어댑터 상태 확인
    try:
        from memory_adapter import MemoryAdapter

        adapter = MemoryAdapter()
        stats = adapter.get_stats()

        print(f"1. Memory Adapter Status:")
        print(f"   - Buffer size: {stats.get('buffer_size', 0)}")
        print(f"   - DB records: {stats.get('db_records', 0)}")
        print(f"   - JSON records: {stats.get('json_records', 0)}")
        print(f"   - Last sync: {stats.get('last_sync', 'unknown')}")

        # 동기화 상태 판단
        buffer_size = stats.get("buffer_size", 0)
        if buffer_size == 0:
            print("   ✅ Memory sync: OK (buffer empty)")
        else:
            print(f"   ⚠️  Memory sync: Pending ({buffer_size} items in buffer)")

    except Exception as e:
        print(f"   ❌ Memory adapter error: {e}")
        return False

    # 2. 파일 상태 확인
    print(f"\n2. File Status:")
    memory_files = [
        "data/memory/memory_buffer.jsonl",
        "data/memory/learning_memory.json",
        "data/memory/velos.db",
    ]

    for file_path in memory_files:
        full_path = ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            mtime = time.ctime(full_path.stat().st_mtime)
            print(f"   ✅ {file_path}: {size} bytes, modified {mtime}")
        else:
            print(f"   ❌ {file_path}: missing")

    # 3. 시스템 헬스 확인
    print(f"\n3. System Health:")
    health_file = ROOT / "data/logs/system_health.json"
    if health_file.exists():
        try:
            with open(health_file, "r", encoding="utf-8") as f:
                health = json.load(f)

            memory_tick_ok = health.get("memory_tick_last_ok", False)
            memory_tick_ts = health.get("memory_tick_last_ts", 0)

            if memory_tick_ok:
                print(f"   ✅ Memory tick: OK (last: {time.ctime(memory_tick_ts)})")
            else:
                print(f"   ❌ Memory tick: Failed")

        except Exception as e:
            print(f"   ❌ Health file error: {e}")
    else:
        print(f"   ❌ Health file: missing")

    # 4. 최근 메모리 활동 확인
    print(f"\n4. Recent Memory Activity:")
    try:
        recent_data = adapter.get_recent_data(limit=5)
        if recent_data:
            print(f"   - Recent entries: {len(recent_data)}")
            latest = recent_data[0]
            print(f"   - Latest entry: {latest.get('ts', 'unknown')}")
            print(f"   - Latest content: {latest.get('content', '')[:50]}...")
        else:
            print(f"   - No recent entries")
    except Exception as e:
        print(f"   ❌ Recent data error: {e}")

    print(f"\n=== Memory Sync Check Complete ===")
    return True


if __name__ == "__main__":
    check_memory_sync()
