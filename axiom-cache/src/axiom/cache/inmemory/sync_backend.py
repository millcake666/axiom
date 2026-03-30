"""axiom.cache.inmemory.sync_backend — Synchronous in-memory cache backend."""

from __future__ import annotations

import fnmatch
import threading
import time
from typing import Any

from axiom.cache.base import SyncCacheBackend


class SyncInMemoryCache(SyncCacheBackend):
    """Synchronous in-memory cache using threading.Lock for thread safety."""

    def __init__(self) -> None:
        """Initialize with an empty store."""
        self._store: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Get a value by key, respecting TTL expiry."""
        with self._lock:
            if key not in self._store:
                return None
            value, expire_at = self._store[key]
            if expire_at is not None and time.monotonic() > expire_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store value under key with optional TTL in seconds."""
        with self._lock:
            expire_at = time.monotonic() + ttl if ttl else None
            self._store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        """Remove a single key."""
        with self._lock:
            self._store.pop(key, None)

    def delete_by_pattern(self, pattern: str, params: list[str] | None = None) -> None:
        """Remove keys matching pattern, optionally filtered by param substrings."""
        with self._lock:
            if params:
                keys = [
                    k
                    for k in self._store
                    if fnmatch.fnmatch(k, pattern) and any(p in k for p in params)
                ]
            else:
                keys = [k for k in self._store if fnmatch.fnmatch(k, pattern)]
            for key in keys:
                del self._store[key]

    def delete_all(self) -> None:
        """Remove all keys from the store."""
        with self._lock:
            self._store.clear()

    def exists(self, key: str) -> bool:
        """Return True if the key exists and has not expired."""
        return self.get(key) is not None
