#!/usr/bin/env python3
"""
VELOS Path Manager - Centralized path management for cross-platform compatibility
Provides standardized path resolution for Windows/Linux environments.
"""

import os
from pathlib import Path


class VelosPathManager:
    """Centralized path management for VELOS system"""

    DEFAULT_WINDOWS_ROOT = "C:/giwanos"
    DEFAULT_LINUX_ROOT = str(Path(__file__).resolve().parents[2])

    def __init__(self):
        # Priority: ENV > Legacy ENV > Platform default
        self._root_path = (
            os.environ.get("VELOS_ROOT_PATH")
            or os.environ.get("GIWANOS_ROOT")  # Legacy support
            or (self.DEFAULT_WINDOWS_ROOT if os.name == "nt" else self.DEFAULT_LINUX_ROOT)
        )

    @property
    def root(self) -> str:
        return self._root_path

    def get_path(self, *path_parts: str) -> str:
        return os.path.join(self._root_path, *path_parts)

    def get_data_path(self, *path_parts: str) -> str:
        return self.get_path("data", *path_parts)

    def get_config_path(self, *path_parts: str) -> str:
        return self.get_path("configs", *path_parts)

    def get_memory_path(self, *path_parts: str) -> str:
        return self.get_data_path("memory", *path_parts)

    def get_logs_path(self, *path_parts: str) -> str:
        return self.get_data_path("logs", *path_parts)

    def get_db_path(self, db_name: str = "velos.db") -> str:
        # Environment override for the default DB name
        if db_name == "velos.db":
            env_path = os.environ.get("VELOS_DB_PATH")
            if env_path:
                return env_path
        return self.get_memory_path(db_name)

    def ensure_dir(self, path: str) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_path_dir(self, *path_parts: str) -> str:
        full_path = self.get_path(*path_parts)
        Path(full_path).parent.mkdir(parents=True, exist_ok=True)
        return full_path

    def is_windows_style_path(self, path: str) -> bool:
        return bool(path and len(path) > 2 and path[1:3] == ":/")

    def normalize_path(self, path: str) -> str:
        if not path:
            return path
        if self.is_windows_style_path(path) and path.startswith("C:/giwanos"):
            return path.replace("C:/giwanos", self._root_path)
        return os.path.normpath(path)

    def to_posix_style(self, path: str) -> str:
        return path.replace("\\", "/") if path else path

    def get_environment_info(self) -> dict:
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
    return _path_manager.root


def get_velos_path(*path_parts: str) -> str:
    return _path_manager.get_path(*path_parts)


def get_data_path(*path_parts: str) -> str:
    return _path_manager.get_data_path(*path_parts)


def get_config_path(*path_parts: str) -> str:
    return _path_manager.get_config_path(*path_parts)


def get_memory_path(*path_parts: str) -> str:
    return _path_manager.get_memory_path(*path_parts)


def get_db_path(db_name: str = "velos.db") -> str:
    return _path_manager.get_db_path(db_name)


def normalize_velos_path(path: str) -> str:
    return _path_manager.normalize_path(path)
