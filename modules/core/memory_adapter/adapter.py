# [ACTIVE] VELOS 메모리 어댑터 - 핵심 데이터 관리 모듈
# [ACTIVE] VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.
import os
import json
import time
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

# VELOS 표준 데이터베이스 연결 및 경로 관리
# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

try:
    from ..db_util import db_open
    USE_DB_UTIL = True
except ImportError:
    USE_DB_UTIL = False

try:
    from ..path_manager import get_velos_root, get_memory_path, get_data_path, get_logs_path
    USE_PATH_MANAGER = True
except ImportError:
    USE_PATH_MANAGER = False

# Path initialization with fallback
if USE_PATH_MANAGER:
    ROOT = get_velos_root()
    PATHS = {
        "jsonl": get_memory_path("learning_memory.jsonl"),
        "db":    get_memory_path("velos.db"),
        "lock":  get_memory_path("memory.flush.lock"),
        "log":   get_logs_path("system_health.json"),
    }
else:
    ROOT = get_velos_root() if "get_velos_root" in locals() else "C:/giwanos"
    PATHS = {
        "jsonl": os.path.join(ROOT, "data", "memory", "learning_memory.jsonl"),
        "db":    os.path.join(ROOT, "data", "memory", "velos.db"),
        "lock":  os.path.join(ROOT, "data", "memory", "memory.flush.lock"),
        "log":   os.path.join(ROOT, "data", "logs", "system_health.json"),
    }

os.makedirs(os.path.dirname(PATHS["jsonl"]), exist_ok=True)
os.makedirs(os.path.dirname(PATHS["db"]), exist_ok=True)
os.makedirs(os.path.dirname(PATHS["log"]), exist_ok=True)

_lock = threading.RLock()

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

@contextmanager
def _file_lock(lock_path: str, timeout_sec: int = 10) -> Any:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            with open(lock_path, "x") as f:
                f.write(str(os.getpid()))
            try:
                yield
            finally:
                try:
                    os.remove(lock_path)
                except Exception:
                    pass
            return
        except FileExistsError:
            time.sleep(0.1)
    raise TimeoutError(f"Lock timeout: {lock_path}")

def _ensure_compat_views(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
    CREATE VIEW IF NOT EXISTS memory_compat AS
    SELECT id, ts, role, insight AS text FROM memory;

    CREATE VIEW IF NOT EXISTS memory_roles AS
    SELECT id, ts, role, '' AS source, insight AS text FROM memory;

    CREATE VIEW IF NOT EXISTS memory_text AS
    SELECT id, ts, role, '[]' AS tags, insight AS text_norm FROM memory;
    """)
    con.commit()
    con.close()

def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            role TEXT NOT NULL,         -- 'user' | 'system' 등
            insight TEXT NOT NULL,      -- 요약/인사이트
            raw TEXT,                   -- 원문(raw)
            tags TEXT                   -- JSON array string
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_ts ON memory(ts DESC)")
    conn.commit()

def create_memory_adapter(db_path: Optional[str] = None, **kw: Any) -> "MemoryAdapter":
    db_path = db_path or os.getenv("VELOS_DB_PATH", get_db_path() if "get_db_path" in locals() else get_data_path("memory/velos.db") if "get_data_path" in locals() else "C:/giwanos/data/memory/velos.db")
    if db_path:
        _ensure_compat_views(db_path)
    return MemoryAdapter(db_path=db_path, **kw)

def _backoff_iter(max_tries: int = 5, base: float = 0.2) -> Any:
    for i in range(max_tries):
        yield base * (2 ** i)

class MemoryAdapter:
    def __init__(self, jsonl_path: Optional[str] = None, db_path: Optional[str] = None):
        self.jsonl = jsonl_path or PATHS["jsonl"]
        self.db = db_path or PATHS["db"]
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock = threading.RLock()

        # 호환성 뷰 자동 생성
        _ensure_compat_views(self.db)

    def append_jsonl(self, item: Dict[str, Any]) -> None:
        """
        item = {"from": "user"|"system", "insight": str, "raw": str, "tags": [..], "ts": int}
        ts 없으면 지금 시간.
        """
        with _lock:
            line = dict(item)
            line.setdefault("ts", int(time.time()))
            try:
                with open(self.jsonl, "a", encoding="utf-8") as f:
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")
            finally:
                self._health_update({"last_append_ok": True, "last_append_ts": line["ts"]})

    def flush_jsonl_to_db(self, max_lines: int = 5000) -> int:
        """
        JSONL에서 DB로 옮긴 행 수 반환. 단일 작성자 보장 위해 파일락 사용.
        """
        moved = 0
        with _file_lock(PATHS["lock"], timeout_sec=10):
            lines = []
            if not os.path.exists(self.jsonl):
                self._health_update({"flush_note": "jsonl_missing"})
                return 0

            # JSONL 읽기
            with open(self.jsonl, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if not line.strip():
                        continue
                    lines.append(line)
                    if i + 1 >= max_lines:
                        break

            if not lines:
                return 0

            # DB 기록
            for delay in _backoff_iter():
                try:
                    conn = sqlite3.connect(self.db, timeout=5)
                    _ensure_schema(conn)
                    cur = conn.cursor()
                    for raw in lines:
                        try:
                            obj = json.loads(raw)
                        except Exception:
                            continue
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
                        moved += 1
                    conn.commit()
                    conn.close()
                    break
                except sqlite3.OperationalError:
                    time.sleep(delay)
                except Exception:
                    time.sleep(delay)

            # 옮긴 만큼 JSONL에서 잘라내기(안전한 rewrite)
            if moved > 0:
                self._truncate_jsonl(prefix_count=moved)

            self._health_update({"last_flush_count": moved, "last_flush_ok": True, "last_flush_ts": int(time.time())})
            return moved

    def _truncate_jsonl(self, prefix_count: int) -> None:
        # 큰 파일도 안전하게 처리: 나머지 라인만 다시 씀
        tmp = self.jsonl + ".tmp"
        keep = []
        with open(self.jsonl, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i + 1 > prefix_count:
                    keep.append(line)
        with open(tmp, "w", encoding="utf-8") as fw:
            fw.writelines(keep)
        os.replace(tmp, self.jsonl)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        out = []
        try:
            conn = sqlite3.connect(self.db, timeout=5)
            _ensure_schema(conn)
            cur = conn.cursor()
            for row in cur.execute("SELECT ts, role, insight, raw, tags FROM memory ORDER BY ts DESC LIMIT ?", (limit,)):
                ts, role, insight, raw, tags = row
                try:
                    raw = json.loads(raw) if raw else ""
                    tags = json.loads(tags) if tags else []
                except Exception:
                    pass
                out.append({"ts": ts, "from": role, "insight": insight, "raw": raw, "tags": tags})
            conn.close()
        except Exception:
            pass
        return out

    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if USE_DB_UTIL:
                conn = db_open(self.db)
            else:
                conn = sqlite3.connect(self.db, timeout=5)
            _ensure_schema(conn)
            cur = conn.cursor()
            
            # FTS 테이블 존재 확인
            has_fts = cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_fts'"
            ).fetchone() is not None
            
            if has_fts:
                try:
                    # FTS 검색 시도
                    rows = cur.execute("""
                      SELECT m.id, m.ts, m.role, m.insight, m.raw, m.tags
                      FROM memory_fts f JOIN memory m ON f.rowid = m.id
                      WHERE f.text MATCH ?
                      ORDER BY m.ts DESC
                      LIMIT ?""", (keyword, limit)).fetchall()
                    
                    out = []
                    for row in rows:
                        id_val, ts, role, insight, raw, tags = row
                        try:
                            raw = json.loads(raw) if raw else ""
                            tags = json.loads(tags) if tags else []
                        except Exception:
                            pass
                        out.append({"ts": ts, "from": role, "insight": insight, "raw": raw, "tags": tags})
                    
                    conn.close()
                    return out
                except sqlite3.Error:
                    pass  # FTS 실패 시 LIKE 검색으로 폴백
            
            # LIKE 검색 (폴백)
            q = f"%{keyword}%"
            out = []
            for row in cur.execute(
                "SELECT ts, role, insight, raw, tags FROM memory WHERE insight LIKE ? OR raw LIKE ? ORDER BY ts DESC LIMIT ?",
                (q, q, limit),
            ):
                ts, role, insight, raw, tags = row
                try:
                    raw = json.loads(raw) if raw else ""
                    tags = json.loads(tags) if tags else []
                except Exception:
                    pass
                out.append({"ts": ts, "from": role, "insight": insight, "raw": raw, "tags": tags})
            
            conn.close()
            return out
        except Exception:
            return []

    def get_roles_unified(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        통합된 역할별 쿼리 - 기존의 분리된 user_rows, system_rows 쿼리를 대체

        Returns:
            Dict with 'user' and 'system' keys containing respective rows
        """
        result: Dict[str, List[Dict[str, Any]]] = {"user": [], "system": []}
        try:
            conn = sqlite3.connect(self.db, timeout=5)
            _ensure_schema(conn)
            cur = conn.cursor()

            # 통합된 쿼리로 user와 system 역할을 한 번에 조회
            unified_query = """
                SELECT id, ts, role, source, text
                FROM memory_roles
                WHERE role IN ('user', 'system')
                ORDER BY ts DESC
                LIMIT ?
            """

            rows = cur.execute(unified_query, (limit * 2,)).fetchall()

            # 역할별로 분류
            for row in rows:
                id_val, ts, role, source, text = row
                row_dict = {
                    "id": id_val,
                    "ts": ts,
                    "role": role,
                    "source": source,
                    "text": text
                }

                if role == 'user':
                    result["user"].append(row_dict)
                elif role == 'system':
                    result["system"].append(row_dict)

            # 각 역할별로 limit 개수만큼만 반환
            result["user"] = result["user"][:limit]
            result["system"] = result["system"][:limit]

            conn.close()
        except Exception as e:
            print(f"통합 역할 쿼리 오류: {e}")
        return result

    def _health_update(self, patch: Dict[str, Any]) -> None:
        h = _read_json(PATHS["log"])
        h.update(patch)
        _write_json(PATHS["log"], h)

    def get_stats(self) -> Dict[str, Any]:
        """메모리 통계 반환"""
        stats = {
            "buffer_size": 0,
            "db_records": 0,
            "json_records": 0,
            "last_sync": None
        }

        # JSONL 버퍼 크기
        try:
            if os.path.exists(self.jsonl):
                with open(self.jsonl, "r", encoding="utf-8") as f:
                    stats["buffer_size"] = sum(1 for line in f if line.strip())
        except Exception:
            pass

        # DB 레코드 수
        try:
            conn = sqlite3.connect(self.db, timeout=5)
            _ensure_schema(conn)
            cur = conn.cursor()
            (count,) = cur.execute("SELECT COUNT(*) FROM memory").fetchone()
            stats["db_records"] = count
            conn.close()
        except Exception:
            pass

        # JSON 파일 레코드 수
        try:
            json_path = os.path.join(ROOT, "data", "memory", "learning_memory.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        stats["json_records"] = len(data)
        except Exception:
            pass

        # 마지막 동기화 시간
        try:
            health = _read_json(PATHS["log"])
            stats["last_sync"] = health.get("last_flush_ts")
        except Exception:
            pass

        return stats

if __name__ == "__main__":
    # 자가 검증 테스트
    adapter = MemoryAdapter()

    # 테스트 데이터 추가
    test_item = {
        "from": "user",
        "insight": "VELOS 운영 철학 테스트",
        "raw": "파일명 불변, 자가 검증, 자동 복구 원칙 테스트",
        "tags": ["test", "philosophy"],
        "ts": int(time.time())
    }

    print("=== VELOS MemoryAdapter 자가 검증 테스트 ===")
    print(f"추가할 레코드: {test_item}")

    # JSONL에 추가
    adapter.append_jsonl(test_item)
    print("✅ JSONL 추가 완료")

    # DB로 플러시
    moved = adapter.flush_jsonl_to_db()
    print(f"✅ DB 동기화 완료: {moved}개 레코드")

    # 통계 확인
    stats = adapter.get_stats()
    print(f"메모리 통계: {stats}")

    # 최근 레코드 확인
    recent = adapter.recent(limit=5)
    print(f"최근 레코드: {len(recent)}개")

    print("=== 자가 검증 완료 ===")
