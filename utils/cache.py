"""
Lightweight SQLite-backed cache with TTL expiry.

Used by the services layer to avoid re-hitting OpenAlex / Crossref /
Semantic Scholar for identical queries within a short time window,
which reduces latency and helps stay within fair-use rate limits.
"""

import hashlib
import json
import sqlite3
import threading
import time
from typing import Any
import os
import warnings

from config import CACHE_DB_PATH, CACHE_ENABLED, CACHE_TTL_SECONDS

_lock = threading.Lock()


def _make_key(*parts: str) -> str:
    """Combine key parts into a single deterministic cache key."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SQLiteCache:
    """Simple thread-safe SQLite-backed key/value cache with TTL expiry."""

    def __init__(self, db_path: str = CACHE_DB_PATH, ttl: int = CACHE_TTL_SECONDS):
        self.db_path = db_path
        self.ttl = ttl
        self._disabled = False
        self._mem_cache: dict[str, tuple[float, str]] = {}
        # Ensure parent directory exists and is writable. If we cannot
        # initialize the SQLite DB due to filesystem permissions, fall back
        # to an in-memory cache (safe for CI; avoids failing tests).
        try:
            db_dir = os.path.dirname(self.db_path) or "."
            os.makedirs(db_dir, exist_ok=True)
            self._init_db()
        except (sqlite3.OperationalError, OSError) as exc:
            warnings.warn(
                f"SQLite cache unavailable ({exc!r}); falling back to in-memory cache",
                RuntimeWarning,
            )
            self._disabled = True

    def _init_db(self) -> None:
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, *key_parts: str) -> Any | None:
        """Return the cached value for the given key parts, or None if missing/expired."""
        if not CACHE_ENABLED:
            return None
        key = _make_key(*key_parts)
        if self._disabled:
            entry = self._mem_cache.get(key)
            if not entry:
                return None
            value, created_at = entry
        else:
            with _lock, sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT value, created_at FROM cache WHERE key = ?", (key,)
                ).fetchone()
            if not row:
                return None
            value, created_at = row
        if not row:
            return None
        value, created_at = row
        if time.time() - created_at > self.ttl:
            self.delete(*key_parts)
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def set(self, *key_parts_and_value: Any) -> None:
        """
        Store a value under the given key.
        The final positional argument is the value; all preceding
        arguments form the composite key, e.g. cache.set("search", "ai", results).
        """
        if not CACHE_ENABLED:
            return
        *key_parts, value = key_parts_and_value
        key = _make_key(*key_parts)
        if self._disabled:
            self._mem_cache[key] = (json.dumps(value), time.time())
            return
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time()),
            )
            conn.commit()

    def delete(self, *key_parts: str) -> None:
        key = _make_key(*key_parts)
        if self._disabled:
            self._mem_cache.pop(key, None)
            return
        with _lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()


# Shared singleton cache instance used across all services.
cache = SQLiteCache()
