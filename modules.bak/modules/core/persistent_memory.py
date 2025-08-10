import sqlite3
import json
from modules.core.error_handler import handle_exception

class PersistentMemory:
    def __init__(self, db_path='persistent_memory.db'):
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self._initialize_db()
        except sqlite3.Error as e:
            handle_exception(e, context="PersistentMemory 초기화 실패")

    def _initialize_db(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            handle_exception(e, context="PersistentMemory DB 초기화 실패")

    def set(self, key, value):
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            self.cursor.execute('''
                INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)
            ''', (key, json_value))
            self.conn.commit()
        except (sqlite3.Error, TypeError, json.JSONDecodeError) as e:
            handle_exception(e, context="PersistentMemory 데이터 저장 실패")

    def get(self, key):
        try:
            self.cursor.execute('''
                SELECT value FROM memory WHERE key=?
            ''', (key,))
            result = self.cursor.fetchone()
            return json.loads(result[0]) if result else None
        except (sqlite3.Error, TypeError, json.JSONDecodeError) as e:
            handle_exception(e, context="PersistentMemory 데이터 조회 실패")
            return None

    def remove(self, key):
        try:
            self.cursor.execute('''
                DELETE FROM memory WHERE key=?
            ''', (key,))
            self.conn.commit()
        except sqlite3.Error as e:
            handle_exception(e, context="PersistentMemory 데이터 삭제 실패")


