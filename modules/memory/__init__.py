"""
VELOS Memory Management Package
Handles all memory-related operations including storage, caching, and routing.
"""

# Import manager integration for Phase 3 optimization
try:
    from ..core.import_manager import ensure_velos_imports, import_velos

    _IMPORT_MANAGER_AVAILABLE = True
except ImportError:
    _IMPORT_MANAGER_AVAILABLE = False

__all__ = ["storage", "cache", "router", "ingest"]

__version__ = "2.0.0"
__doc__ = """
VELOS Memory Package - Phase 3 Optimized

This package provides unified memory management for the VELOS system:
- Storage: SQLite and other storage backends
- Cache: High-performance memory caching
- Router: Intelligent query routing
- Ingest: Data ingestion and processing
"""
