# [EXPERIMENT] scripts/check_fts_health.py
import sqlite3
import os

def check_fts_health():
    db_path = 'C:/giwanos/data/velos.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # FTS 테이블 존재 확인
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_fts'")
        fts_exists = cur.fetchone() is not None
        
        if not fts_exists:
            print("FTS status=ERROR, message=memory_fts table not found")
            return
        
        # FTS 테이블 레코드 수 확인
        cur.execute("SELECT COUNT(*) FROM memory_fts")
        fts_rows = cur.fetchone()[0]
        
        # FTS 테이블 구조 확인
        cur.execute("PRAGMA table_info(memory_fts)")
        columns = cur.fetchall()
        has_text_column = any(col[1] == 'text' for col in columns)
        
        # 호환 뷰 확인 (구식 코드 대응)
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='view' AND name='memory_fts_compat'")
        compat_view_exists = cur.fetchone() is not None
        
        # 테스트 검색 실행
        test_success = False
        try:
            cur.execute("SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH 'test'")
            test_count = cur.fetchone()[0]
            test_success = True
        except sqlite3.Error:
            test_success = False
        
        conn.close()
        
        # 상태 판정 (호환 뷰 고려)
        if fts_exists and (has_text_column or compat_view_exists) and test_success:
            print(f"FTS status=OK, rows={fts_rows}")
        else:
            issues = []
            if not fts_exists:
                issues.append("table_missing")
            if not has_text_column and not compat_view_exists:
                issues.append("Deprecated column reference: expected insight/raw, got text")
            if not test_success:
                issues.append("search_failed")
            print(f"FTS status=ERROR, issues={','.join(issues)}, rows={fts_rows}")
            
    except Exception as e:
        print(f"FTS status=ERROR, message={str(e)}")

if __name__ == "__main__":
    check_fts_health()


