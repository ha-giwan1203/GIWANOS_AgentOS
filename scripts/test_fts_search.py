# [EXPERIMENT] scripts/test_fts_search.py
import sqlite3

def test_fts_search(search_term="검색어"):
    conn = sqlite3.connect('C:/giwanos/data/velos.db')
    cur = conn.cursor()
    
    print(f"=== FTS Search Test: '{search_term}' ===")
    
    try:
        # FTS 검색 실행
        query = "SELECT rowid, text FROM memory_fts WHERE memory_fts MATCH ?"
        cur.execute(query, (search_term,))
        results = cur.fetchall()
        
        print(f"Found {len(results)} results:")
        for i, (rowid, text) in enumerate(results[:10], 1):  # 최대 10개만 출력
            print(f"{i}. rowid={rowid}, text={text[:100]}...")
            
        if len(results) > 10:
            print(f"... and {len(results) - 10} more results")
            
    except Exception as e:
        print(f"Search error: {e}")
    
    conn.close()

if __name__ == "__main__":
    # 기본 검색어로 테스트
    test_fts_search("검색어")
    
    # 추가 테스트
    print("\n" + "="*50)
    test_fts_search("test_user")
    
    print("\n" + "="*50)
    test_fts_search("ingest")
