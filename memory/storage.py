"""Persistent SQLite storage entry point for University Research Assistant."""

import importlib.util
from pathlib import Path

_storage_path = Path(__file__).resolve().parent.parent / "solutions" / "03-memory" / "storage.py"
_spec = importlib.util.spec_from_file_location("storage_mod", _storage_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

SQLiteMemoryStorage = _mod.SQLiteMemoryStorage

__all__ = ["SQLiteMemoryStorage"]
