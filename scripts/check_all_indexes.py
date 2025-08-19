# [EXPERIMENT] VELOS 인덱스 검증 - 데이터베이스 무결성 검사
# [EXPERIMENT] scripts/check_all_indexes.py
import sqlite3

def check_all_indexes():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== All Indexes Check ===")
    
    # 모든 인덱스 확인
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
    indexes = cur.fetchall()
    
    print("Indexes found:")
    for name, sql in indexes:
        print(f"\n=== Index: {name} ===")
        if sql:
            print(f"SQL: {sql}")
    
    conn.close()

if __name__ == "__main__":
    check_all_indexes()
