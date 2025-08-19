# [EXPERIMENT] VELOS 뷰 검증 - 데이터베이스 뷰 검사
# [EXPERIMENT] scripts/check_all_views.py
import sqlite3

def check_all_views():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== All Views Check ===")
    
    # 모든 뷰 확인
    cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cur.fetchall()
    
    print("Views found:")
    for view in views:
        view_name = view[0]
        print(f"\n=== View: {view_name} ===")
        
        # 뷰 정의 확인
        cur.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view_name,))
        sql = cur.fetchone()
        if sql:
            print(f"Definition: {sql[0]}")
        
        # 뷰에서 데이터 확인 (최대 3개)
        try:
            cur.execute(f"SELECT * FROM {view_name} LIMIT 3")
            rows = cur.fetchall()
            print(f"Sample data ({len(rows)} rows):")
            for i, row in enumerate(rows, 1):
                print(f"  {i}. {row}")
        except Exception as e:
            print(f"Error querying view: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_all_views()
