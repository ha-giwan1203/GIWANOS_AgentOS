
import sqlite3
import json

class PersistentMemory:
    def __init__(self, db_path='persistent_memory.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def set(self, key, value):
        self.cursor.execute('''
            INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)
        ''', (key, json.dumps(value)))
        self.conn.commit()

    def get(self, key):
        self.cursor.execute('''
            SELECT value FROM memory WHERE key=?
        ''', (key,))
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result else None

    def exists(self, key):
        self.cursor.execute('''
            SELECT 1 FROM memory WHERE key=?
        ''', (key,))
        return self.cursor.fetchone() is not None

    def remove(self, key):
        self.cursor.execute('''
            DELETE FROM memory WHERE key=?
        ''', (key,))
        self.conn.commit()

    def get_related_data(self, query):
        self.cursor.execute('SELECT key, value FROM memory')
        return {key: json.loads(value) for key, value in self.cursor.fetchall()}


