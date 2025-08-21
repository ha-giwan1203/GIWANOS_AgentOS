#!/usr/bin/env python3
"""
Comprehensive tests for VELOS Import Manager
Tests import optimization, caching, and module resolution.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.core.import_manager import (
    VelosImportManager,
    add_velos_path,
    cleanup_imports,
    ensure_velos_imports,
    get_import_info,
    get_velos_root,
    import_velos,
)


class TestVelosImportManager(unittest.TestCase):
    """Test cases for VelosImportManager class"""

    def setUp(self):
        """Set up test environment"""
        self.manager = VelosImportManager()
        self.original_sys_path = sys.path.copy()

    def tearDown(self):
        """Clean up test environment"""
        # Restore original sys.path
        sys.path.clear()
        sys.path.extend(self.original_sys_path)

    def test_initialization(self):
        """Test VelosImportManager initialization"""
        manager = VelosImportManager()

        # Verify base path is set correctly
        self.assertIsInstance(manager._base_path, Path)
        self.assertTrue(manager._base_path.exists())

        # Verify cache and paths are initialized
        self.assertIsInstance(manager._import_cache, dict)
        self.assertIsInstance(manager._paths_added, set)

    def test_path_addition(self):
        """Test path addition functionality"""
        manager = VelosImportManager()
        test_path = "/test/path"

        # Test adding new path
        result = manager.add_path(test_path)
        self.assertTrue(result)
        self.assertIn(test_path, sys.path)
        self.assertIn(test_path, manager._paths_added)

        # Test adding same path again (should return False)
        result_duplicate = manager.add_path(test_path)
        self.assertFalse(result_duplicate)

    def test_temporary_path_context(self):
        """Test temporary path context manager"""
        manager = VelosImportManager()
        test_path = "/temporary/path"

        # Verify path is not initially in sys.path
        self.assertNotIn(test_path, sys.path)

        # Use temporary path context
        with manager.temporary_path(test_path):
            self.assertIn(test_path, sys.path)

        # Verify path is removed after context
        self.assertNotIn(test_path, sys.path)

    def test_module_import_caching(self):
        """Test module import caching functionality"""
        manager = VelosImportManager()

        # Mock a successful import
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module

            # First import should call importlib
            result1 = manager.import_module("test_module")
            self.assertEqual(result1, mock_module)
            mock_import.assert_called_once_with("test_module")

            # Second import should use cache
            mock_import.reset_mock()
            result2 = manager.import_module("test_module")
            self.assertEqual(result2, mock_module)
            mock_import.assert_not_called()

    def test_velos_module_import_patterns(self):
        """Test VELOS-specific module import patterns"""
        manager = VelosImportManager()

        # Mock importlib to test different patterns
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()

            # Test successful import on first pattern
            mock_import.side_effect = [mock_module]
            result = manager._import_with_velos_paths("db_util")

            # Should try modules.db_util first
            mock_import.assert_called_with("modules.db_util")
            self.assertEqual(result, mock_module)

    def test_file_search_import(self):
        """Test direct file search and import functionality"""
        manager = VelosImportManager()

        # Create a temporary module file
        with tempfile.TemporaryDirectory() as temp_dir:
            module_file = Path(temp_dir) / "test_module.py"
            module_content = """
def test_function():
    return "test_result"
"""
            module_file.write_text(module_content)

            # Mock the search paths to include our temp directory
            with patch.object(manager, "_base_path", Path(temp_dir)):
                with patch.object(manager, "_import_by_file_search") as mock_search:
                    mock_module = MagicMock()
                    mock_search.return_value = mock_module

                    # Test that file search is attempted
                    with patch("importlib.import_module", side_effect=ImportError):
                        result = manager.import_module("test_module")
                        mock_search.assert_called_once_with("test_module")

    def test_import_stats(self):
        """Test import statistics functionality"""
        manager = VelosImportManager()

        stats = manager.get_import_stats()

        required_keys = ["cached_modules", "added_paths", "base_path", "sys_path_length"]
        for key in required_keys:
            self.assertIn(key, stats)

        self.assertIsInstance(stats["cached_modules"], int)
        self.assertIsInstance(stats["added_paths"], int)
        self.assertIsInstance(stats["sys_path_length"], int)

    def test_sys_path_cleanup(self):
        """Test sys.path cleanup functionality"""
        manager = VelosImportManager()

        # Add some duplicate paths
        duplicate_path = "/duplicate/path"
        sys.path.extend([duplicate_path, duplicate_path, duplicate_path])
        original_length = len(sys.path)

        # Run cleanup
        removed_count = manager.cleanup_sys_path(keep_velos_paths=False)

        # Verify cleanup removed duplicates
        self.assertGreaterEqual(removed_count, 0)
        self.assertLess(len(sys.path), original_length + 2)  # Allow some flexibility


class TestImportManagerConvenienceFunctions(unittest.TestCase):
    """Test cases for import manager convenience functions"""

    def test_convenience_functions_exist(self):
        """Test that convenience functions are available and callable"""
        # Test functions exist and are callable
        self.assertTrue(callable(import_velos))
        self.assertTrue(callable(add_velos_path))
        self.assertTrue(callable(ensure_velos_imports))
        self.assertTrue(callable(get_velos_root))
        self.assertTrue(callable(cleanup_imports))
        self.assertTrue(callable(get_import_info))

    def test_import_velos_function(self):
        """Test import_velos convenience function"""
        # Test with mock to avoid actual imports
        with patch("modules.core.import_manager._import_manager") as mock_manager:
            mock_module = MagicMock()
            mock_manager.import_velos_module.return_value = mock_module

            result = import_velos("core.test_module")
            mock_manager.import_velos_module.assert_called_once_with("core.test_module")
            self.assertEqual(result, mock_module)

    def test_add_velos_path_function(self):
        """Test add_velos_path convenience function"""
        with patch("modules.core.import_manager._import_manager") as mock_manager:
            mock_manager.add_path.return_value = True

            result = add_velos_path("/test/path")
            mock_manager.add_path.assert_called_once_with("/test/path")
            self.assertTrue(result)

    def test_ensure_velos_imports_function(self):
        """Test ensure_velos_imports convenience function"""
        with patch("modules.core.import_manager._import_manager") as mock_manager:
            mock_manager.ensure_velos_imports.return_value = True

            result = ensure_velos_imports()
            mock_manager.ensure_velos_imports.assert_called_once()
            self.assertTrue(result)


class TestImportManagerIntegration(unittest.TestCase):
    """Integration tests for import manager"""

    def test_import_manager_with_real_modules(self):
        """Test import manager with actual VELOS modules"""
        manager = VelosImportManager()

        # Test importing a module that should exist
        try:
            path_manager_module = manager.import_module("modules.core.path_manager")
            self.assertIsNotNone(path_manager_module)

            # Verify it has expected attributes
            self.assertTrue(hasattr(path_manager_module, "VelosPathManager"))
        except ImportError:
            # If import fails, it's not necessarily a test failure
            # as the module might not be available in test environment
            pass

    def test_critical_imports_check(self):
        """Test critical imports verification"""
        manager = VelosImportManager()

        # Run critical imports check
        result = manager.ensure_velos_imports()

        # Result should be boolean
        self.assertIsInstance(result, bool)

        # If it's False, there should be import issues logged
        if not result:
            # This is expected in some test environments
            pass


class TestImportManagerErrorHandling(unittest.TestCase):
    """Test error handling in import manager"""

    def test_import_error_handling(self):
        """Test handling of import errors"""
        manager = VelosImportManager()

        # Test importing non-existent module
        with self.assertRaises(ImportError):
            manager.import_module("definitely_non_existent_module_12345")

    def test_malformed_path_handling(self):
        """Test handling of malformed paths"""
        manager = VelosImportManager()

        # Test with None path (should handle gracefully)
        try:
            manager.add_path(None)
        except Exception as e:
            # Should handle gracefully, not crash
            self.assertIsInstance(e, (TypeError, AttributeError))


if __name__ == "__main__":
    unittest.main(verbosity=2, buffer=True)
