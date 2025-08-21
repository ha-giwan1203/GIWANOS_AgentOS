import os
import sqlite3

DB = os.getenv("VELOS_DB_PATH", r"C:\giwanos\data\memory\velos.db")


def ensure_fts():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # 기존 FTS 테이블 구조 확인
    try:
        fts_cols = cur.execute("PRAGMA table_info('memory_fts')").fetchall()
        print(f"현재 FTS 컬럼: {[col[1] for col in fts_cols]}")

        # text 컬럼이 없으면 테이블 재생성
        if not any(col[1] == 'text' for col in fts_cols):
            print("FTS 테이블을 표준 스키마로 재생성합니다...")
            cur.execute("DROP TABLE IF EXISTS memory_fts")
    except Exception:
        print("FTS 테이블이 없습니다. 새로 생성합니다...")

    # FTS5 테이블 생성 (표준 스키마)
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(text)")

    # 기존 트리거 삭제
    cur.execute("DROP TRIGGER IF EXISTS trg_mem_ai")
    cur.execute("DROP TRIGGER IF EXISTS trg_mem_ad")
    cur.execute("DROP TRIGGER IF EXISTS trg_mem_au")

    # INSERT 트리거 (안전한 패턴)
    cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_ai AFTER INSERT ON memory BEGIN
      INSERT INTO memory_fts(rowid, text) VALUES (new.id, COALESCE(new.insight, new.raw, ''));
    END;""")

    # DELETE 트리거 (안전한 패턴)
    cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_ad AFTER DELETE ON memory BEGIN
      INSERT INTO memory_fts(memory_fts, rowid, text) VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
    END;""")

    # UPDATE 트리거 (안전한 패턴)
    cur.execute("""CREATE TRIGGER IF NOT EXISTS trg_mem_au AFTER UPDATE ON memory BEGIN
      INSERT INTO memory_fts(memory_fts, rowid, text) VALUES('delete', old.id, COALESCE(old.insight, old.raw, ''));
      INSERT INTO memory_fts(rowid, text) VALUES (new.id, COALESCE(new.insight, new.raw, ''));
    END;""")

    # 누락된 데이터 백필 (안전한 패턴)
    cur.execute("""INSERT INTO memory_fts(rowid, text)
                   SELECT id, COALESCE(insight, raw, '')
                   FROM memory
                   WHERE id NOT IN (SELECT rowid FROM memory_fts)""")

    # 최적화
    cur.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")

    # 결과 확인 (개선된 패턴)
    total_mem = cur.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
    total_fts = cur.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
    print(f"VELOS 메모리 시스템 종합 통계:")
    print(f"  총 레코드: {total_mem}개")
    print(f"  FTS 인덱스: {total_fts}개")

    con.commit()
    con.close()


if __name__ == "__main__":
    print("VELOS FTS 부트스트랩 시작...")
    ensure_fts()
    print("✅ FTS 부트스트랩 완료")
