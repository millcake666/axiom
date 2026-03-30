"""axiom.cache.redis.sync_backend — Synchronous Redis cache backend."""

from __future__ import annotations

from typing import Any

from axiom.cache.base import SyncCacheBackend
from axiom.cache.serialization import SerializationStrategy
from axiom.cache.serialization.orjson_strategy import OrjsonStrategy
from axiom.redis.sync_client import SyncRedisClient


class SyncRedisCache(SyncCacheBackend):
    """Synchronous Redis-backed cache backend with pluggable serialization."""

    def __init__(
        self,
        client: SyncRedisClient,
        serializer: SerializationStrategy | None = None,
    ) -> None:
        """Initialize with a SyncRedisClient and optional serializer."""
        self._client = client
        self._serializer = serializer or OrjsonStrategy()

    def get(self, key: str) -> Any | None:
        """Retrieve and deserialize a value by key."""
        data = self._client.get(key)
        if data is None:
            return None
        return self._serializer.deserialize(data)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Serialize and store value under key with optional TTL."""
        data = self._serializer.serialize(value)
        self._client.set(key, data, ttl=ttl)

    def delete(self, key: str) -> None:
        """Remove a single key."""
        self._client.delete(key)

    def delete_by_pattern(self, pattern: str, params: list[str] | None = None) -> None:
        """Remove keys matching pattern, optionally filtered by param substrings."""
        for key in self._client.scan_iter(pattern):
            if params is None or any(p in key for p in params):
                self._client.delete(key)

    def delete_all(self) -> None:
        """Flush all keys from Redis."""
        self._client.flushall()

    def exists(self, key: str) -> bool:
        """Return True if the key exists in Redis."""
        return self._client.exists(key)
