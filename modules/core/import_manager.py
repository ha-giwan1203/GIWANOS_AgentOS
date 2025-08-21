#!/usr/bin/env python3
"""
VELOS Import Manager - Centralized module import and path management
Replaces scattered sys.path manipulations with unified import resolution.
"""

import importlib
import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, List, Optional, Union


class VelosImportManager:
    """Centralized import management for VELOS system"""

    def __init__(self):
        self._base_path = Path(__file__).parent.parent.parent  # /home/user/webapp
        self._import_cache = {}
        self._paths_added = set()
        self._initialize_standard_paths()

    def _initialize_standard_paths(self):
        """Initialize standard VELOS module paths"""
        standard_paths = [
            self._base_path,  # Root
            self._base_path / "modules",  # Modules directory
            self._base_path / "modules" / "core",  # Core modules
            self._base_path / "modules" / "memory",  # Memory modules
            self._base_path / "configs",  # Configuration modules
        ]

        for path in standard_paths:
            self.add_path(str(path))

    def add_path(self, path: Union[str, Path], permanent: bool = True) -> bool:
        """Add a path to sys.path if not already present"""
        path_str = str(Path(path).resolve())

        if path_str not in self._paths_added and path_str not in sys.path:
            sys.path.insert(0, path_str)
            if permanent:
                self._paths_added.add(path_str)
            return True
        return False

    @contextmanager
    def temporary_path(self, path: Union[str, Path]):
        """Temporarily add a path to sys.path"""
        path_str = str(Path(path).resolve())
        added = self.add_path(path_str, permanent=False)
        try:
            yield
        finally:
            if added and path_str in sys.path:
                sys.path.remove(path_str)

    def import_module(self, module_name: str, package: Optional[str] = None) -> Any:
        """Import a module with caching"""
        cache_key = f"{package}.{module_name}" if package else module_name

        if cache_key in self._import_cache:
            return self._import_cache[cache_key]

        try:
            if package:
                module = importlib.import_module(f".{module_name}", package)
            else:
                module = importlib.import_module(module_name)

            self._import_cache[cache_key] = module
            return module

        except ImportError as e:
            # Try with VELOS paths
            return self._import_with_velos_paths(module_name, package)

    def _import_with_velos_paths(self, module_name: str, package: Optional[str] = None) -> Any:
        """Import module using VELOS-specific path resolution"""
        # Common VELOS module patterns
        velos_patterns = [
            f"modules.{module_name}",
            f"modules.core.{module_name}",
            f"modules.memory.{module_name}",
            f"modules.automation.{module_name}",
            f"configs.{module_name}",
        ]

        for pattern in velos_patterns:
            try:
                module = importlib.import_module(pattern)
                cache_key = f"{package}.{module_name}" if package else module_name
                self._import_cache[cache_key] = module
                return module
            except ImportError:
                continue

        # Last resort: try to find the module file directly
        return self._import_by_file_search(module_name)

    def _import_by_file_search(self, module_name: str) -> Any:
        """Search for module file and import it directly"""
        # Search common locations
        search_paths = [
            self._base_path / "modules",
            self._base_path / "modules" / "core",
            self._base_path / "modules" / "memory",
            self._base_path / "modules" / "automation",
            self._base_path / "scripts",
        ]

        for search_path in search_paths:
            module_file = search_path / f"{module_name}.py"
            if module_file.exists():
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._import_cache[module_name] = module
                    return module

        raise ImportError(f"Cannot find module: {module_name}")

    def import_velos_module(self, module_path: str) -> Any:
        """Import a VELOS module using dot notation (e.g., 'core.db_util')"""
        parts = module_path.split(".")

        if len(parts) == 1:
            # Single module name
            return self.import_module(parts[0])

        # Multi-part module path
        try:
            # Try as modules.{path}
            full_path = f"modules.{module_path}"
            return importlib.import_module(full_path)
        except ImportError:
            # Try individual parts
            return self.import_module(parts[-1], f"modules.{'.'.join(parts[:-1])}")

    def get_velos_root(self) -> Path:
        """Get VELOS root directory"""
        return self._base_path

    def resolve_velos_path(self, *path_parts: str) -> Path:
        """Resolve a path relative to VELOS root"""
        return self._base_path.joinpath(*path_parts)

    def ensure_velos_imports(self) -> bool:
        """Ensure all VELOS modules can be imported"""
        critical_modules = [
            "modules.core.path_manager",
            "modules.core.db_util",
            "modules.memory.storage.sqlite_store",
            "configs",
        ]

        success = True
        for module in critical_modules:
            try:
                importlib.import_module(module)
            except ImportError as e:
                print(f"⚠️ Failed to import {module}: {e}")
                success = False

        return success

    def get_import_stats(self) -> dict:
        """Get import manager statistics"""
        return {
            "cached_modules": len(self._import_cache),
            "added_paths": len(self._paths_added),
            "base_path": str(self._base_path),
            "sys_path_length": len(sys.path),
        }

    def cleanup_sys_path(self, keep_velos_paths: bool = True) -> int:
        """Clean up sys.path by removing duplicate and unnecessary paths"""
        original_count = len(sys.path)

        # Keep track of paths to preserve
        preserve_paths = set()
        if keep_velos_paths:
            preserve_paths.update(self._paths_added)

        # Remove duplicates while preserving order
        seen = set()
        cleaned_path = []

        for path in sys.path:
            if path not in seen:
                if (
                    not keep_velos_paths
                    or path in preserve_paths
                    or not path.startswith(str(self._base_path))
                ):
                    cleaned_path.append(path)
                    seen.add(path)

        sys.path.clear()
        sys.path.extend(cleaned_path)

        return original_count - len(sys.path)


# Global instance
_import_manager = VelosImportManager()


# Convenience functions
def import_velos(module_path: str) -> Any:
    """Import a VELOS module (e.g., import_velos('core.db_util'))"""
    return _import_manager.import_velos_module(module_path)


def add_velos_path(path: Union[str, Path]) -> bool:
    """Add a path for VELOS imports"""
    return _import_manager.add_path(path)


def velos_import_context(path: Union[str, Path]):
    """Context manager for temporary import path"""
    return _import_manager.temporary_path(path)


def ensure_velos_imports() -> bool:
    """Ensure all critical VELOS modules can be imported"""
    return _import_manager.ensure_velos_imports()


def get_velos_root() -> Path:
    """Get VELOS root path"""
    return _import_manager.get_velos_root()


def cleanup_imports() -> int:
    """Clean up sys.path duplicates"""
    return _import_manager.cleanup_sys_path()


def get_import_info() -> dict:
    """Get import manager information"""
    return _import_manager.get_import_stats()


# Backward compatibility aliases
velos_root = get_velos_root
velos_path = _import_manager.resolve_velos_path

if __name__ == "__main__":
    # Self-validation test
    print("=== VELOS Import Manager Self-Validation ===")

    manager = VelosImportManager()

    print(f"VELOS root: {manager.get_velos_root()}")
    print(f"Added paths: {len(manager._paths_added)}")

    # Test critical imports
    print("\nTesting critical imports:")
    success = manager.ensure_velos_imports()
    print(f"All critical imports successful: {success}")

    # Test import functions
    print("\nTesting import functions:")
    try:
        path_manager = import_velos("core.path_manager")
        print("✅ Successfully imported core.path_manager")
    except Exception as e:
        print(f"❌ Failed to import core.path_manager: {e}")

    # Statistics
    stats = manager.get_import_stats()
    print(f"\nImport Manager Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test sys.path cleanup
    original_length = len(sys.path)
    removed = manager.cleanup_sys_path()
    print(
        f"\nSys.path cleanup: removed {removed} duplicates (was {original_length}, now {len(sys.path)})"
    )

    print("=== Self-validation complete ===")
