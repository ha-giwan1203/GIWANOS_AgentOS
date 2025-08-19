# [EXPERIMENT] scripts/fts_repair.py
import sqlite3, sys, os, textwrap

DB = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")

DDL_FTS = """
-- 1) 기존 FTS 관련 객체 깨끗이 제거
-- 트리거/뷰 먼저 드랍 (존재하면)
{drop_triggers}
{drop_views}
-- FTS 본체 드랍
DROP TABLE IF EXISTS memory_fts;

-- 2) FTS5 재생성 (외부 컨텐츠, 단일 text 컬럼)
CREATE VIRTUAL TABLE memory_fts USING fts5(
  text,
  content='memory',
  content_rowid='id',
  tokenize='unicode61 remove_diacritics 2',
  prefix='2 3 4'
);

-- 3) 트리거 재생성
CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;

CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
  VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
END;

CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
  INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
  VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
  INSERT INTO memory_fts(rowid, insight, raw)
  VALUES (new.id, COALESCE(new.insight, new.raw, ''));
END;
"""

def compile_options(conn):
    return {r[0] for r in conn.execute("PRAGMA compile_options;")}

def list_objs(conn, typ, like):
    sql = "SELECT name FROM sqlite_master WHERE type=? AND sql LIKE ?"
    return [r[0] for r in conn.execute(sql, (typ, f"%{like}%"))]

def drop_list_sql(names, kind):
    if not names:
        return "-- none\n"
    stmts = []
    for n in names:
        # SQLite는 IF EXISTS가 드물게 안 먹히는 버전이 있다. 안전하게 명시 드랍
        stmts.append(f"DROP {kind} {n};")
    return "\n".join(stmts) + "\n"

def main():
    print(f"[fts_repair] DB: {DB}")
    conn = sqlite3.connect(DB)
    conn.isolation_level = None  # 수동 트랜잭션
    cur = conn.cursor()

    # 0) FTS5 지원 확인
    opts = compile_options(conn)
    if not any(o.startswith("FTS5") for o in opts):
        raise SystemExit("이 SQLite 빌드는 FTS5가 켜져 있지 않습니다. 다른 바이너리를 쓰세요.")

    # 0.5) 기본 테이블 존재 확인
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory';")
    if not cur.fetchone():
        raise SystemExit("기본 테이블 'memory'가 없습니다. 스키마부터 복구하세요.")

    # 1) 현재 FTS/트리거/뷰 조사
    triggers = list_objs(conn, "trigger", "memory_fts")
    views    = list_objs(conn, "view",    "memory_fts")
    print(f"[fts_repair] drop targets: triggers={triggers}, views={views}")

    drops_trg = drop_list_sql(triggers, "TRIGGER")
    drops_vw  = drop_list_sql(views, "VIEW")

    # 2) 트랜잭션 시작
    cur.execute("BEGIN IMMEDIATE;")
    try:
        ddl = DDL_FTS.format(drop_triggers=drops_trg, drop_views=drops_vw)
        cur.executescript(ddl)

        # 3) 전체 재색인
        cur.execute("""
            INSERT INTO memory_fts(rowid, insight, raw)
            SELECT id, COALESCE(insight, raw, '')
            FROM memory
            WHERE COALESCE(insight, raw, '') <> '';
        """)

        # 4) 최적화
        cur.execute("INSERT INTO memory_fts(memory_fts) VALUES ('optimize');")

        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        raise
    finally:
        # 검증 리포트
        cnt = cur.execute("SELECT COUNT(*) FROM memory_fts;").fetchone()[0]
        sample = cur.execute("SELECT insight, raw FROM memory_fts LIMIT 3;").fetchall()
        print(f"[fts_repair] fts rows: {cnt}")
        for i, r in enumerate(sample, 1):
            print(f"[fts_repair] sample {i}: rowid={r[0]} text={r[1]!r}")
        conn.close()

if __name__ == "__main__":
    try:
        main()
        print("[fts_repair] OK")
    except Exception as e:
        print("[fts_repair] FAILED:", e)
        sys.exit(1)


