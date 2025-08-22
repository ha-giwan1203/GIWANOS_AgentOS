#!/usr/bin/env python3
"""
Comprehensive tests for VELOS Path Manager
Tests cross-platform path management, normalization, and environment handling.
"""

import os

# Import the module under test
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.core.path_manager import (
    VelosPathManager,
    get_config_path,
    get_data_path,
    get_db_path,
    get_memory_path,
    get_velos_path,
    get_velos_root,
    normalize_velos_path,
)


class TestVelosPathManager(unittest.TestCase):
    """Test cases for VelosPathManager class"""

    def setUp(self):
        """Set up test environment"""
        self.manager = VelosPathManager()
        self.test_env_vars = {}

    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment variables
        for key, value in self.test_env_vars.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_initialization(self):
        """Test VelosPathManager initialization"""
        manager = VelosPathManager()
        self.assertIsInstance(manager.root, str)
        self.assertTrue(len(manager.root) > 0)

    def test_root_path_resolution(self):
        """Test root path resolution with different environments"""
        # Test with VELOS_ROOT_PATH environment variable
        with patch.dict(os.environ, {"VELOS_ROOT_PATH": "/test/path"}):
            manager = VelosPathManager()
            self.assertEqual(manager.root, "/test/path")

    def test_path_construction(self):
        """Test path construction methods"""
        manager = VelosPathManager()

        # Test basic path construction
        path = manager.get_path("test", "subdir")
        expected = os.path.join(manager.root, "test", "subdir")
        self.assertEqual(path, expected)

        # Test data path
        data_path = manager.get_data_path("logs", "test.log")
        expected_data = os.path.join(manager.root, "data", "logs", "test.log")
        self.assertEqual(data_path, expected_data)

        # Test config path
        config_path = manager.get_config_path("settings.yaml")
        expected_config = os.path.join(manager.root, "configs", "settings.yaml")
        self.assertEqual(config_path, expected_config)

    def test_database_path_handling(self):
        """Test database path resolution"""
        manager = VelosPathManager()

        # Test default database path
        db_path = manager.get_db_path()
        self.assertTrue(db_path.endswith("velos.db"))

        # Test with VELOS_DB_PATH environment variable
        with patch.dict(os.environ, {"VELOS_DB_PATH": "/custom/db/path.db"}):
            custom_db_path = manager.get_db_path()
            self.assertEqual(custom_db_path, "/custom/db/path.db")

    def test_path_normalization(self):
        """Test path normalization functionality"""
        manager = VelosPathManager()

        # Test Windows path normalization
        windows_path = "C:\giwanos/data/memory/test.db"
        normalized = manager.normalize_path(windows_path)

        # Should replace C:\giwanos with current root
        self.assertNotIn("C:\giwanos", normalized)
        self.assertIn(manager.root, normalized)

        # Test path with backslashes (only if it starts with C:\giwanos pattern)
        mixed_path = "C:\giwanos/data/test"  # Use forward slash version
        normalized_mixed = manager.normalize_path(mixed_path)
        self.assertIn(manager.root, normalized_mixed)

    def test_windows_path_detection(self):
        """Test Windows-style path detection"""
        manager = VelosPathManager()

        self.assertTrue(manager.is_windows_style_path("C:/test/path"))
        self.assertTrue(manager.is_windows_style_path("D:/another/path"))
        self.assertFalse(manager.is_windows_style_path("/unix/path"))
        self.assertFalse(manager.is_windows_style_path("relative/path"))
        self.assertFalse(manager.is_windows_style_path(""))

    def test_posix_path_conversion(self):
        """Test POSIX path conversion"""
        manager = VelosPathManager()

        # Test backslash to forward slash conversion
        self.assertEqual(manager.to_posix_style("test\\path"), "test/path")
        self.assertEqual(manager.to_posix_style("test/path"), "test/path")
        self.assertEqual(manager.to_posix_style(""), "")

    def test_directory_creation(self):
        """Test directory creation functionality"""
        manager = VelosPathManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "test", "nested", "file.txt")
            result_path = manager.ensure_dir(test_path)

            self.assertEqual(result_path, test_path)
            self.assertTrue(os.path.exists(os.path.dirname(test_path)))

    def test_environment_info(self):
        """Test environment information gathering"""
        manager = VelosPathManager()

        env_info = manager.get_environment_info()

        required_keys = ["root_path", "platform", "is_windows", "environment_vars"]
        for key in required_keys:
            self.assertIn(key, env_info)

        self.assertIsInstance(env_info["is_windows"], bool)
        self.assertIsInstance(env_info["environment_vars"], dict)


class TestPathManagerFunctions(unittest.TestCase):
    """Test cases for path manager convenience functions"""

    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        # Test that functions return strings
        self.assertIsInstance(get_velos_root(), str)
        self.assertIsInstance(get_velos_path("test"), str)
        self.assertIsInstance(get_data_path("logs"), str)
        self.assertIsInstance(get_config_path("settings.yaml"), str)
        self.assertIsInstance(get_memory_path("test.db"), str)
        self.assertIsInstance(get_db_path(), str)

    def test_path_normalization_function(self):
        """Test standalone path normalization function"""
        # Test that function handles various inputs
        self.assertIsInstance(normalize_velos_path("C:\giwanos/test"), str)
        self.assertIsInstance(normalize_velos_path("/unix/path"), str)
        self.assertIsInstance(normalize_velos_path(""), str)


class TestPathManagerIntegration(unittest.TestCase):
    """Integration tests for path manager with other system components"""

    def test_path_manager_with_environment_variables(self):
        """Test path manager behavior with various environment setups"""
        # Test different environment variable combinations
        test_scenarios = [
            {"VELOS_ROOT_PATH": "/test/root"},
            {"VELOS_DB_PATH": "/test/db.sqlite"},
            {"VELOS_ROOT_PATH": "/test/root", "VELOS_DB_PATH": "/test/custom.db"},
        ]

        for env_vars in test_scenarios:
            with patch.dict(os.environ, env_vars, clear=False):
                manager = VelosPathManager()

                # Verify root path is set correctly
                if "VELOS_ROOT_PATH" in env_vars:
                    self.assertEqual(manager.root, env_vars["VELOS_ROOT_PATH"])

                # Verify database path is set correctly
                if "VELOS_DB_PATH" in env_vars:
                    self.assertEqual(manager.get_db_path(), env_vars["VELOS_DB_PATH"])


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
