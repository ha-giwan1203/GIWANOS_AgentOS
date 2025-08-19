# [EXPERIMENT] VELOS 객체 검증 - 데이터베이스 스키마 검사
# [EXPERIMENT] scripts/check_all_objects.py
import sqlite3

def check_all_objects():
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print("=== All Database Objects ===")
    
    # 모든 객체 확인
    cur.execute("SELECT name, type, sql FROM sqlite_master WHERE name IS NOT NULL ORDER BY type, name")
    objects = cur.fetchall()
    
    for name, obj_type, sql in objects:
        print(f"\n=== {obj_type.upper()}: {name} ===")
        if sql:
            print(f"SQL: {sql[:200]}...")
    
    conn.close()

if __name__ == "__main__":
    check_all_objects()
