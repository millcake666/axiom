"""axiom.cache.redis.async_backend — Async Redis cache backend."""

from __future__ import annotations

from typing import Any

from axiom.cache.base import AsyncCacheBackend
from axiom.cache.serialization import SerializationStrategy
from axiom.cache.serialization.orjson_strategy import OrjsonStrategy
from axiom.redis.async_client import AsyncRedisClient


class AsyncRedisCache(AsyncCacheBackend):
    """Async Redis-backed cache backend with pluggable serialization."""

    def __init__(
        self,
        client: AsyncRedisClient,
        serializer: SerializationStrategy | None = None,
    ) -> None:
        """Initialize with an AsyncRedisClient and optional serializer."""
        self._client = client
        self._serializer = serializer or OrjsonStrategy()

    async def get(self, key: str) -> Any | None:
        """Retrieve and deserialize a value by key."""
        data = await self._client.get(key)
        if data is None:
            return None
        return self._serializer.deserialize(data)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Serialize and store value under key with optional TTL."""
        data = self._serializer.serialize(value)
        await self._client.set(key, data, ttl=ttl)

    async def delete(self, key: str) -> None:
        """Remove a single key."""
        await self._client.delete(key)

    async def delete_by_pattern(self, pattern: str, params: list[str] | None = None) -> None:
        """Remove keys matching pattern, optionally filtered by param substrings."""
        async for key in self._client.scan_iter(pattern):
            if params is None or any(p in key for p in params):
                await self._client.delete(key)

    async def delete_all(self) -> None:
        """Flush all keys from Redis."""
        await self._client.flushall()

    async def exists(self, key: str) -> bool:
        """Return True if the key exists in Redis."""
        return await self._client.exists(key)
