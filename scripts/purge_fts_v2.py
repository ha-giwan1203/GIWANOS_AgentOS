# [EXPERIMENT] VELOS FTS v2 정리 시스템 - FTS v2 테이블 정리 스크립트
import sqlite3, os, sys

DB = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")

def main():
    print(f"[purge_v2] DB={DB}")
    con = sqlite3.connect(DB)
    con.isolation_level = None
    cur = con.cursor()

    cur.execute("BEGIN IMMEDIATE;")
    try:
        # v2를 참조하는 트리거/뷰 삭제
        rows = cur.execute("""
          SELECT type, name FROM sqlite_master
          WHERE (lower(sql) LIKE '%memory_fts_v2%')
            AND type IN ('trigger','view')
        """).fetchall()
        for typ, name in rows:
            cur.execute(f"DROP {typ.upper()} IF EXISTS {name};")

        # v2 테이블과 섀도 테이블 삭제
        for name in ("memory_fts_v2",):
            for shadow in (name, f"{name}_data", f"{name}_idx", f"{name}_docsize", f"{name}_config"):
                cur.execute(f"DROP TABLE IF EXISTS {shadow};")

        cur.execute("COMMIT;")
    except Exception:
        cur.execute("ROLLBACK;")
        raise
    finally:
        # 확인
        left = cur.execute("""
          SELECT type, name FROM sqlite_master
          WHERE name LIKE 'memory_fts_v2%' OR lower(sql) LIKE '%memory_fts_v2%'
        """).fetchall()
        print("[purge_v2] remains:", left)
        con.close()
        print("[purge_v2] OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[purge_v2] FAILED:", e)
        sys.exit(1)
