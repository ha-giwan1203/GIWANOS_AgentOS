import sqlite3

conn = sqlite3.connect('data/velos.db')
cur = conn.cursor()

# 사용자가 제안한 쿼리 실행
cur.execute("""
SELECT id, ts, role, source, text
FROM memory_roles
WHERE role = 'system'
ORDER BY ts DESC
LIMIT 10
""")

results = cur.fetchall()

print("시스템 역할 최근 10개 레코드:")
print("=" * 60)

for id_val, ts, role, source, text in results:
    print(f"ID {id_val}: [{ts}] {role} - {text[:60]}...")

print(f"\n총 {len(results)}개 레코드")

conn.close()
