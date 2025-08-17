# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변, 실패 시 안전 복구.
import os, sys, json, time
from typing import Dict, Any

ROOT = "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

from modules.core.memory_adapter import MemoryAdapter

HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")

def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_json(path: str, obj: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def memory_tick():
    """메모리 틱 처리: JSONL에서 DB로 플러시 및 상태 업데이트"""
    try:
        adapter = MemoryAdapter()

        # JSONL에서 DB로 플러시
        moved = adapter.flush_jsonl_to_db()

        # 통계 수집
        stats = adapter.get_stats()

        # 헬스 로그 업데이트
        h = _read_json(HEALTH)
        h.update({
            "memory_tick_last_ts": int(time.time()),
            "memory_tick_last_moved": moved,
            "memory_tick_last_ok": True,
            "memory_tick_stats": stats
        })
        _write_json(HEALTH, h)

        print(f"[MEMORY_TICK] 플러시 완료: {moved}개 레코드, 버퍼={stats['buffer_size']}, DB={stats['db_records']}")
        return True

    except Exception as e:
        # 실패 시에도 헬스 로그 업데이트
        h = _read_json(HEALTH)
        h.update({
            "memory_tick_last_ts": int(time.time()),
            "memory_tick_last_ok": False,
            "memory_tick_last_error": str(e)
        })
        _write_json(HEALTH, h)

        print(f"[MEMORY_TICK] 오류: {e}")
        return False

if __name__ == "__main__":
    print("=== VELOS Memory Tick ===")
    success = memory_tick()
    sys.exit(0 if success else 1)
