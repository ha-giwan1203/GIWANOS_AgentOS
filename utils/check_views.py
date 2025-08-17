import sqlite3
import os

# 환경 변수 설정
os.environ['VELOS_DB'] = 'C:/giwanos/data/velos.db'

# 데이터베이스 연결
con = sqlite3.connect('C:/giwanos/data/velos.db')
cur = con.cursor()

# 뷰 목록 확인
cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
views = cur.fetchall()
print("뷰 목록:", views)

# 테이블 목록 확인
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("테이블 목록:", tables)

con.close()
