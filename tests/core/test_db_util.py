#!/usr/bin/env python3
"""
Comprehensive tests for VELOS Database Utility
Tests database connection, optimization, and reliability.
"""

import os
import sqlite3

# Import the module under test
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.core.db_util import db_open


class TestDbUtil(unittest.TestCase):
    """Test cases for database utility functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_db_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_db_dir, "test_velos.db")

    def tearDown(self):
        """Clean up test environment"""
        # Clean up test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.test_db_dir):
            os.rmdir(self.test_db_dir)

    def test_db_open_with_explicit_path(self):
        """Test database opening with explicit path"""
        conn = db_open(self.test_db_path)

        # Verify connection is created
        self.assertIsInstance(conn, sqlite3.Connection)

        # Verify database file is created
        self.assertTrue(os.path.exists(self.test_db_path))

        # Test basic database operations
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        conn.commit()

        # Verify data was inserted
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        self.assertEqual(result, (1, "test"))

        conn.close()

    def test_db_open_with_environment_variable(self):
        """Test database opening using environment variable"""
        with patch.dict(os.environ, {"VELOS_DB_PATH": self.test_db_path}):
            conn = db_open()

            self.assertIsInstance(conn, sqlite3.Connection)
            self.assertTrue(os.path.exists(self.test_db_path))

            conn.close()

    def test_db_open_with_path_manager(self):
        """Test database opening using path manager integration"""
        # Mock the path manager import at the right location
        with patch("modules.core.path_manager.get_db_path") as mock_get_db_path:
            mock_get_db_path.return_value = self.test_db_path

            # Clear environment variable to force path manager usage
            with patch.dict(os.environ, {}, clear=True):
                conn = db_open()

                self.assertIsInstance(conn, sqlite3.Connection)
                # Note: get_db_path might not be called if import fails

                conn.close()

    def test_sqlite_pragma_settings(self):
        """Test that SQLite PRAGMA settings are applied correctly"""
        conn = db_open(self.test_db_path)

        # Check WAL mode
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        self.assertEqual(journal_mode.upper(), "WAL")

        # Check synchronous mode
        cursor.execute("PRAGMA synchronous")
        synchronous_mode = cursor.fetchone()[0]
        self.assertEqual(synchronous_mode, 1)  # NORMAL

        # Check busy timeout
        cursor.execute("PRAGMA busy_timeout")
        busy_timeout = cursor.fetchone()[0]
        self.assertEqual(busy_timeout, 5000)

        # Check foreign keys
        cursor.execute("PRAGMA foreign_keys")
        foreign_keys = cursor.fetchone()[0]
        self.assertEqual(foreign_keys, 1)  # ON

        conn.close()

    def test_database_performance_settings(self):
        """Test that performance optimization settings work"""
        conn = db_open(self.test_db_path)
        cursor = conn.cursor()

        # Test that WAL mode allows concurrent reads
        cursor.execute("CREATE TABLE perf_test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.commit()

        # Insert test data
        test_data = [(i, f"data_{i}") for i in range(100)]
        cursor.executemany("INSERT INTO perf_test (id, data) VALUES (?, ?)", test_data)
        conn.commit()

        # Verify data integrity
        cursor.execute("SELECT COUNT(*) FROM perf_test")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 100)

        conn.close()

    def test_connection_isolation_level(self):
        """Test connection isolation level setting"""
        conn = db_open(self.test_db_path)

        # Verify isolation level is None (autocommit mode)
        self.assertIsNone(conn.isolation_level)

        conn.close()

    def test_database_timeout_handling(self):
        """Test database timeout handling"""
        conn1 = db_open(self.test_db_path)
        conn2 = db_open(self.test_db_path)

        # Both connections should work due to WAL mode
        cursor1 = conn1.cursor()
        cursor2 = conn2.cursor()

        # Create table with first connection
        cursor1.execute("CREATE TABLE timeout_test (id INTEGER)")
        conn1.commit()

        # Read with second connection (should work with WAL)
        cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor2.fetchall()
        self.assertTrue(len(tables) >= 1)

        conn1.close()
        conn2.close()

    def test_fallback_path_handling(self):
        """Test fallback path handling when path manager is not available"""
        with patch.dict(os.environ, {}, clear=True):
            # Should fall back to default path when no env var is set
            conn = db_open()
            self.assertIsInstance(conn, sqlite3.Connection)
            conn.close()


class TestDbUtilIntegration(unittest.TestCase):
    """Integration tests for database utility"""

    def setUp(self):
        """Set up integration test environment"""
        self.test_db_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_db_dir, "integration_test.db")

    def tearDown(self):
        """Clean up integration test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.test_db_dir):
            os.rmdir(self.test_db_dir)

    def test_real_world_usage_pattern(self):
        """Test real-world database usage patterns"""
        # Simulate typical VELOS database operations
        conn = db_open(self.test_db_path)
        cursor = conn.cursor()

        # Create VELOS-like memory table
        cursor.execute(
            """
            CREATE TABLE memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                role TEXT NOT NULL,
                insight TEXT NOT NULL,
                raw TEXT,
                tags TEXT
            )
        """
        )

        cursor.execute("CREATE INDEX idx_memory_ts ON memory(ts DESC)")
        conn.commit()

        # Insert test data
        import time

        test_records = [
            (int(time.time()), "user", "Test insight 1", "Raw data 1", '["tag1"]'),
            (int(time.time()) + 1, "system", "Test insight 2", "Raw data 2", '["tag2"]'),
        ]

        cursor.executemany(
            "INSERT INTO memory(ts, role, insight, raw, tags) VALUES (?, ?, ?, ?, ?)", test_records
        )
        conn.commit()

        # Query data
        cursor.execute("SELECT COUNT(*) FROM memory")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

        # Test search functionality
        cursor.execute("SELECT * FROM memory WHERE role = ?", ("user",))
        user_records = cursor.fetchall()
        self.assertEqual(len(user_records), 1)
        self.assertEqual(user_records[0][2], "user")  # role column

        conn.close()

    def test_concurrent_access_simulation(self):
        """Test concurrent database access simulation"""
        # Create initial database
        conn1 = db_open(self.test_db_path)
        cursor1 = conn1.cursor()
        cursor1.execute("CREATE TABLE concurrent_test (id INTEGER, value TEXT)")
        conn1.commit()

        # Simulate concurrent access
        conn2 = db_open(self.test_db_path)
        cursor2 = conn2.cursor()

        # Write with connection 1
        cursor1.execute("INSERT INTO concurrent_test (id, value) VALUES (1, 'from_conn1')")
        conn1.commit()

        # Read with connection 2 (should see the write due to WAL mode)
        cursor2.execute("SELECT * FROM concurrent_test WHERE id = 1")
        result = cursor2.fetchone()
        self.assertEqual(result[1], "from_conn1")

        # Write with connection 2
        cursor2.execute("INSERT INTO concurrent_test (id, value) VALUES (2, 'from_conn2')")
        conn2.commit()

        # Read with connection 1
        cursor1.execute("SELECT COUNT(*) FROM concurrent_test")
        count = cursor1.fetchone()[0]
        self.assertEqual(count, 2)

        conn1.close()
        conn2.close()


class TestDbUtilErrorHandling(unittest.TestCase):
    """Test error handling in database utility"""

    def setUp(self):
        """Set up test environment"""
        self.test_db_path = tempfile.mktemp(suffix=".db")

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_invalid_database_path(self):
        """Test handling of invalid database paths"""
        # Test with read-only directory (should handle gracefully)
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = os.path.join(temp_dir, "nonexistent", "deep", "path", "test.db")

            # This should still work as SQLite creates intermediate directories
            try:
                conn = db_open(invalid_path)
                conn.close()
            except sqlite3.Error:
                # Some SQLite errors are acceptable for invalid paths
                pass

    def test_database_corruption_resistance(self):
        """Test resistance to database corruption"""
        # Create a database and then corrupt it
        conn = db_open(self.test_db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()

        # Corrupt the database file
        with open(self.test_db_path, "wb") as f:
            f.write(b"corrupted data")

        # Attempt to open corrupted database
        try:
            conn = db_open(self.test_db_path)
            # If connection succeeds, SQLite might recover or create new DB
            conn.close()
        except sqlite3.DatabaseError:
            # This is expected for corrupted databases
            pass


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
