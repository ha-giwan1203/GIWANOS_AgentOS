#!/usr/bin/env python3
# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


"""
VELOS Path Manager - Centralized path management for cross-platform compatibility
Provides standardized path resolution for Windows/Linux environments.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union


class VelosPathManager:
    """Centralized path management for VELOS system"""

    # Default paths for different platforms
    DEFAULT_WINDOWS_ROOT = get_velos_root() if "get_velos_root" in locals() else "/home/user/webapp"
    DEFAULT_LINUX_ROOT = "/home/user/webapp"

    def __init__(self):
        self._root_path = None
        self._initialize_root()

    def _initialize_root(self):
        """Initialize root path based on environment and platform"""
        # Priority: ENV > Platform detection > Fallback
        self._root_path = (
            os.environ.get("VELOS_ROOT_PATH")
            or os.environ.get("GIWANOS_ROOT")  # Legacy support
            or (self.DEFAULT_WINDOWS_ROOT if os.name == "nt" else self.DEFAULT_LINUX_ROOT)
        )

    @property
    def root(self) -> str:
        """Get the root path for VELOS system"""
        return self._root_path

    def get_path(self, *path_parts: str) -> str:
        """Get a path relative to VELOS root"""
        return os.path.join(self._root_path, *path_parts)

    def get_data_path(self, *path_parts: str) -> str:
        """Get a path in the data directory"""
        return self.get_path("data", *path_parts)

    def get_config_path(self, *path_parts: str) -> str:
        """Get a path in the configs directory"""
        return self.get_path("configs", *path_parts)

    def get_memory_path(self, *path_parts: str) -> str:
        """Get a path in the memory directory"""
        return self.get_data_path("memory", *path_parts)

    def get_logs_path(self, *path_parts: str) -> str:
        """Get a path in the logs directory"""
        return self.get_data_path("logs", *path_parts)

    def get_db_path(self, db_name: str = "velos.db") -> str:
        """Get database path (prioritizes environment variable)"""
        # Check for specific DB environment variable first
        if db_name == "velos.db":
            env_path = os.environ.get("VELOS_DB_PATH")
            if env_path:
                return env_path

        # Fallback to standard memory path
        return self.get_memory_path(db_name)

    def ensure_dir(self, path: str) -> str:
        """Ensure directory exists and return the path"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_path_dir(self, *path_parts: str) -> str:
        """Ensure directory for a path exists and return the full path"""
        full_path = self.get_path(*path_parts)
        Path(full_path).parent.mkdir(parents=True, exist_ok=True)
        return full_path

    def is_windows_style_path(self, path: str) -> bool:
        """Check if path is Windows-style (C:/ format)"""
        return bool(path and len(path) > 2 and path[1:3] == ":/")

    def normalize_path(self, path: str) -> str:
        """Normalize path for current platform"""
        if not path:
            return path

        # Convert Windows paths to current platform
        if self.is_windows_style_path(path):
            if path.startswith("/home/user/webapp"):
                # Replace /home/user/webapp with current root
                return path.replace("/home/user/webapp", self._root_path)

        # Normalize separators
        return os.path.normpath(path)

    def to_posix_style(self, path: str) -> str:
        """Convert path to POSIX style (forward slashes)"""
        return path.replace("\\", "/") if path else path

    def get_environment_info(self) -> dict:
        """Get current path environment information"""
        return {
            "root_path": self._root_path,
            "platform": os.name,
            "is_windows": os.name == "nt",
            "environment_vars": {
                "VELOS_ROOT_PATH": os.environ.get("VELOS_ROOT_PATH"),
                "VELOS_DB_PATH": os.environ.get("VELOS_DB_PATH"),
                "GIWANOS_ROOT": os.environ.get("GIWANOS_ROOT"),
            },
        }


# Global instance for easy access
_path_manager = VelosPathManager()


# Convenience functions for backward compatibility
def get_velos_root() -> str:
    """Get VELOS root path"""
    return _path_manager.root


def get_velos_path(*path_parts: str) -> str:
    """Get path relative to VELOS root"""
    return _path_manager.get_path(*path_parts)


def get_data_path(*path_parts: str) -> str:
    """Get path in data directory"""
    return _path_manager.get_data_path(*path_parts)


def get_config_path(*path_parts: str) -> str:
    """Get path in configs directory"""
    return _path_manager.get_config_path(*path_parts)


def get_memory_path(*path_parts: str) -> str:
    """Get path in memory directory"""
    return _path_manager.get_memory_path(*path_parts)


def get_db_path(db_name: str = "velos.db") -> str:
    """Get database path"""
    return _path_manager.get_db_path(db_name)


def normalize_velos_path(path: str) -> str:
    """Normalize VELOS path for current platform"""
    return _path_manager.normalize_path(path)


if __name__ == "__main__":
    # Self-validation test
    print("=== VELOS Path Manager Self-Validation ===")

    manager = VelosPathManager()

    print(f"Root path: {manager.root}")
    print(f"DB path: {manager.get_db_path()}")
    print(f"Memory path: {manager.get_memory_path('test.json')}")
    print(f"Config path: {manager.get_config_path('settings.yaml')}")
    print(f"Logs path: {manager.get_logs_path('system.log')}")

    # Test path normalization
    test_paths = [
        (
            get_db_path()
            if "get_db_path" in locals()
            else (
                get_data_path("memory/velos.db")
                if "get_data_path" in locals()
                else "/home/user/webapp/data/memory/velos.db"
            )
        ),
        (
            get_config_path("settings.yaml")
            if "get_config_path" in locals()
            else "/home/user/webapp/configs/settings.yaml"
        ),
        "/some/absolute/path",
        "relative/path",
    ]

    print("\nPath normalization tests:")
    for test_path in test_paths:
        normalized = manager.normalize_path(test_path)
        print(f"  {test_path} → {normalized}")

    # Environment info
    print(f"\nEnvironment info:")
    env_info = manager.get_environment_info()
    for key, value in env_info.items():
        print(f"  {key}: {value}")

    print("=== Self-validation complete ===")
