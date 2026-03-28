# [EXPERIMENT] VELOS FTS v2 재구성 시스템 - FTS v2 테이블 재구성 스크립트
import sqlite3, os, sys

DB = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
FTS_NAME = "memory_fts_v2"  # 새 이름로 간다. 구 FTS와 충돌 방지.
BASE = "memory"

def main():
    print(f"[rebuild] DB={DB}, FTS={FTS_NAME}")
    con = sqlite3.connect(DB)
    con.isolation_level = None
    cur = con.cursor()

    # 0) FTS5 지원 확인
    try:
        opts = [r[0] for r in cur.execute("PRAGMA compile_options;").fetchall()]
    except Exception:
        opts = []
    if not any("FTS5" in x for x in opts):
        print("[rebuild] 경고: compile_options에 FTS5 표시는 없지만, 시도는 진행합니다.")

    # 1) 유령 객체 삭제 (기존 이름 memory_fts와 그 섀도들, 관련 트리거/뷰)
    cur.execute("BEGIN IMMEDIATE;")
    try:
        # drop triggers/views referencing memory_fts*
        rows = cur.execute("""
          SELECT type, name FROM sqlite_master
          WHERE (lower(sql) LIKE '%memory_fts%' OR lower(sql) LIKE '%memory_fts_v2%')
            AND type IN ('trigger','view')
        """).fetchall()
        for t, n in rows:
            cur.execute(f"DROP {t.upper()} IF EXISTS {n};")

        # drop old fts tables (both names) and possible shadows
        for name in ("memory_fts","memory_fts_v2"):
            for shadow in (name, f"{name}_data", f"{name}_idx", f"{name}_docsize", f"{name}_config"):
                cur.execute(f"DROP TABLE IF EXISTS {shadow};")

        cur.execute("COMMIT;")
    except Exception as e:
        cur.execute("ROLLBACK;")
        raise

    # 2) 새 FTS 생성 (외부 컨텐츠)
    ddl = f"""
    CREATE VIRTUAL TABLE {FTS_NAME} USING fts5(
      text,                          -- 단일 통합 텍스트
      content='{BASE}',              -- 외부 컨텐츠
      content_rowid='id',
      tokenize = 'unicode61 remove_diacritics 2',
      prefix='2 3 4'
    );
    """
    cur.executescript(ddl)

    # 3) 트리거를 새 FTS에 맞춰 재생성
    cur.executescript(f"""
    CREATE TRIGGER trg_{BASE}_ai_v2 AFTER INSERT ON {BASE} BEGIN
      INSERT INTO {FTS_NAME}(rowid, text)
      VALUES (new.id, COALESCE(new.insight, new.raw, ''));
    END;

    CREATE TRIGGER trg_{BASE}_ad_v2 AFTER DELETE ON {BASE} BEGIN
      INSERT INTO {FTS_NAME}({FTS_NAME}, rowid, text)
      VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
    END;

    CREATE TRIGGER trg_{BASE}_au_v2 AFTER UPDATE ON {BASE} BEGIN
      INSERT INTO {FTS_NAME}({FTS_NAME}, rowid, text)
      VALUES ('delete', old.id, COALESCE(old.insight, old.raw, ''));
      INSERT INTO {FTS_NAME}(rowid, text)
      VALUES (new.id, COALESCE(new.insight, new.raw, ''));
    END;
    """)

    # 4) 전체 재색인
    cur.execute(f"""
      INSERT INTO {FTS_NAME}(rowid, text)
      SELECT id, COALESCE(insight, raw, '')
      FROM {BASE}
      WHERE COALESCE(insight, raw, '') <> '';
    """)
    cur.execute(f"INSERT INTO {FTS_NAME}({FTS_NAME}) VALUES ('optimize');")

    # 5) 검증
    cnt = cur.execute(f"SELECT COUNT(*) FROM {FTS_NAME};").fetchone()[0]
    sample = cur.execute(f"SELECT rowid, substr(text,1,60) FROM {FTS_NAME} LIMIT 3;").fetchall()
    print("[rebuild] rows in FTS:", cnt)
    for i, r in enumerate(sample, 1):
        print(f"[rebuild] sample {i}:", r)

    con.close()
    print("[rebuild] OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[rebuild] FAILED:", e)
        sys.exit(1)
