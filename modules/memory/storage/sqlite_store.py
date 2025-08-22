# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.
from __future__ import annotations
import os
import sqlite3
import json
import time
import contextlib
from pathlib import Path
from typing import Optional


def _env(name: str, default: Optional[str] = None) -> str:
    """VELOS 환경 변수 로딩: ENV > configs/settings.yaml > C:\giwanos 순서"""
    v = os.getenv(name, default)
    if not v:
        # 설정 파일에서 로드 시도
        try:
            import yaml
            config_path = Path(os.getenv("VELOS_ROOT", "/workspace")) / "configs" / "settings.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    v = config.get(name, default)
        except Exception:
            pass

        if not v:
            # 기본값 설정
            if name == "VELOS_DB":
                v = os.path.join(os.getenv("VELOS_ROOT", "/workspace"), "data", "velos.db")
            else:
                raise RuntimeError(f"Missing env: {name}")
    return v

def connect_db() -> sqlite3.Connection:
    db_path = Path(_env("VELOS_DB"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path), check_same_thread=False, isolation_level=None)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    cur.execute("PRAGMA mmap_size=268435456;")
    cur.execute("PRAGMA foreign_keys=ON;")
    cur.execute("PRAGMA busy_timeout=5000;")  # 5초
    return con

SCHEMA = """
-- 기존 VELOS 메모리 테이블 (호환성 유지)
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    role TEXT NOT NULL,         -- 'user' | 'system' 등
    insight TEXT NOT NULL,      -- 요약/인사이트
    raw TEXT,                   -- 원문(raw)
    tags TEXT                   -- JSON array string
);

-- 기존 인덱스
CREATE INDEX IF NOT EXISTS idx_memory_ts ON memory(ts DESC);

-- FTS5 가상 테이블 (전체 텍스트 검색용)
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    insight, raw, content='memory', content_rowid='id', tokenize='unicode61'
);

-- FTS 트리거들
CREATE TRIGGER IF NOT EXISTS trg_mem_ai AFTER INSERT ON memory BEGIN
    INSERT INTO memory_fts(rowid, insight, raw) VALUES (new.id, new.insight, new.raw);
END;

CREATE TRIGGER IF NOT EXISTS trg_mem_ad AFTER DELETE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
    VALUES('delete', old.id, old.insight, old.raw);
END;

CREATE TRIGGER IF NOT EXISTS trg_mem_au AFTER UPDATE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
    VALUES('delete', old.id, old.insight, old.raw);
    INSERT INTO memory_fts(rowid, insight, raw) VALUES (new.id, new.insight, new.raw);
END;

-- 크로스프로세스 락 테이블
CREATE TABLE IF NOT EXISTS locks(
    name TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    ts INTEGER NOT NULL
);
"""

def init_schema(con: sqlite3.Connection) -> None:
    # 기존 FTS 테이블이 있으면 삭제 (스키마 변경 시)
    try:
        con.execute("DROP TABLE IF EXISTS memory_fts")
    except Exception:
        pass

    con.executescript(SCHEMA)

@contextlib.contextmanager
def advisory_lock(con: sqlite3.Connection, name: str, owner: str, ttl: int = 60):
    """SQLite 테이블을 이용한 크로스프로세스 락"""
    start = time.time()
    while True:
        try:
            with con:
                con.execute("INSERT INTO locks(name, owner, ts) VALUES(?,?,?)",
                            (name, owner, int(time.time())))
            break
        except sqlite3.IntegrityError:
            # 이미 잡혀있으면 만료된 락 청소 후 재시도
            with con:
                con.execute("DELETE FROM locks WHERE name=? AND ts<?",
                           (name, int(time.time()) - ttl))
            if time.time() - start > ttl:
                raise TimeoutError(f"lock timeout: {name}")
            time.sleep(0.1)
    try:
        yield
    finally:
        with con:
            con.execute("DELETE FROM locks WHERE name=?", (name,))


class VelosMemoryStore:
    """VELOS 메모리 저장소 - FTS5 검색 및 크로스프로세스 락 지원"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _env("VELOS_DB")
        self.con = None

    def __enter__(self):
        self.con = connect_db()
        init_schema(self.con)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con:
            self.con.close()

    def insert_memory(self, ts: int, role: str, insight: str,
                     raw: str = "", tags: list = None) -> int:
        """메모리 삽입 - FTS 자동 인덱싱"""
        if tags is None:
            tags = []

        cur = self.con.cursor()
        cur.execute(
            "INSERT INTO memory(ts, role, insight, raw, tags) VALUES (?, ?, ?, ?, ?)",
            (ts, role, insight, raw, json.dumps(tags, ensure_ascii=False))
        )
        self.con.commit()
        return cur.lastrowid

    def search_fts(self, query: str, limit: int = 50) -> list:
        """FTS5 전체 텍스트 검색"""
        cur = self.con.cursor()
        results = []

        # FTS 검색 실행
        for row in cur.execute(
            "SELECT id, ts, role, insight, raw, tags FROM memory "
            "WHERE id IN (SELECT rowid FROM memory_fts WHERE memory_fts MATCH ?) "
            "ORDER BY ts DESC LIMIT ?",
            (query, limit)
        ):
            id_, ts, role, insight, raw, tags = row
            try:
                tags = json.loads(tags) if tags else []
            except Exception:
                tags = []

            results.append({
                "id": id_, "ts": ts, "from": role, "insight": insight,
                "raw": raw, "tags": tags
            })

        return results

    def get_recent(self, limit: int = 20) -> list:
        """최근 메모리 조회"""
        cur = self.con.cursor()
        results = []

        for row in cur.execute(
            "SELECT id, ts, role, insight, raw, tags FROM memory "
            "ORDER BY ts DESC LIMIT ?",
            (limit,)
        ):
            id_, ts, role, insight, raw, tags = row
            try:
                tags = json.loads(tags) if tags else []
            except Exception:
                tags = []

            results.append({
                "id": id_, "ts": ts, "from": role, "insight": insight,
                "raw": raw, "tags": tags
            })

        return results


if __name__ == "__main__":
    # 자가 검증 테스트
    print("=== VELOS SQLite Store 자가 검증 테스트 ===")

    try:
        # DB 연결 테스트
        con = connect_db()
        print("✅ DB 연결 성공")

        # 스키마 초기화
        init_schema(con)
        print("✅ 스키마 초기화 완료")

        # 락 테스트
        with advisory_lock(con, "test_lock", "test_owner", ttl=10):
            print("✅ Advisory lock 테스트 성공")

        con.close()
        print("=== 자가 검증 완료 ===")

    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        raise
