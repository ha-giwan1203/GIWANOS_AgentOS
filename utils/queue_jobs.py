import os, sqlite3, json
db = os.getenv("VELOS_DB", "C:\\giwanos\\velos.db")
con = sqlite3.connect(db); cur = con.cursor()
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("decide", json.dumps({"task":"테스트 입력","notify":True}, ensure_ascii=False), 10))
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("report", json.dumps({"period":"weekly"}, ensure_ascii=False), 100))
cur.execute("INSERT INTO job_queue(kind,payload,priority) VALUES (?,?,?)",
            ("notify", json.dumps({"msg":"테스트 알림"}, ensure_ascii=False), 100))
con.commit(); con.close()
print("[OK] queued decide/report/notify")
