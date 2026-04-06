"""axiom.redis.async_client — Async Redis client."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as aioredis
from axiom.redis.exception import RedisOperationError
from axiom.redis.settings import RedisSettings


class AsyncRedisClient:
    """Async Redis client wrapping redis.asyncio."""

    def __init__(self, client: aioredis.Redis | aioredis.RedisCluster) -> None:
        """Initialize with an existing async Redis client."""
        self._client = client

    @property
    def raw(self) -> aioredis.Redis | aioredis.RedisCluster:
        """Return the underlying async Redis client."""
        return self._client

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if key does not exist."""
        try:
            return await self._client.get(key)
        except Exception as exc:
            raise RedisOperationError(f"GET failed for key '{key}'") from exc

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a key to value with optional TTL in seconds."""
        try:
            if ttl is not None:
                await self._client.set(key, value, ex=ttl)
            else:
                await self._client.set(key, value)
        except Exception as exc:
            raise RedisOperationError(f"SET failed for key '{key}'") from exc

    async def delete(self, *keys: str) -> None:
        """Delete one or more keys."""
        try:
            if keys:
                await self._client.delete(*keys)
        except Exception as exc:
            raise RedisOperationError(f"DELETE failed for keys {keys}") from exc

    async def exists(self, key: str) -> bool:
        """Return True if the key exists."""
        try:
            result = await self._client.exists(key)
            return bool(result)
        except Exception as exc:
            raise RedisOperationError(f"EXISTS failed for key '{key}'") from exc

    async def expire(self, key: str, seconds: int) -> None:
        """Set expiry on a key."""
        try:
            await self._client.expire(key, seconds)
        except Exception as exc:
            raise RedisOperationError(f"EXPIRE failed for key '{key}'") from exc

    async def ttl(self, key: str) -> int:
        """Return TTL in seconds for a key. Returns -2 if key doesn't exist, -1 if no TTL."""
        try:
            result = await self._client.ttl(key)
            return int(result)
        except Exception as exc:
            raise RedisOperationError(f"TTL failed for key '{key}'") from exc

    async def scan_iter(self, pattern: str) -> AsyncIterator[str]:
        """Async generator yielding keys matching the given pattern."""
        try:
            async for key in self._client.scan_iter(match=pattern):
                if isinstance(key, bytes):
                    yield key.decode()
                else:
                    yield str(key)
        except Exception as exc:
            raise RedisOperationError(f"SCAN failed for pattern '{pattern}'") from exc

    async def flushall(self) -> None:
        """Flush all keys from the current database."""
        try:
            await self._client.flushall()
        except Exception as exc:
            raise RedisOperationError("FLUSHALL failed") from exc

    async def close(self) -> None:
        """Close the Redis connection."""
        try:
            await self._client.aclose()
        except Exception as exc:
            raise RedisOperationError("CLOSE failed") from exc


def create_async_redis_client(settings: RedisSettings) -> AsyncRedisClient:
    """Create an AsyncRedisClient from settings."""
    kwargs: dict[str, Any] = {
        "decode_responses": settings.REDIS_DECODE_RESPONSES,
    }
    if settings.REDIS_MAX_CONNECTIONS is not None:
        kwargs["max_connections"] = settings.REDIS_MAX_CONNECTIONS
    if settings.REDIS_SOCKET_TIMEOUT is not None:
        kwargs["socket_timeout"] = settings.REDIS_SOCKET_TIMEOUT

    if settings.REDIS_USE_CLUSTER:
        client: aioredis.Redis | aioredis.RedisCluster = aioredis.RedisCluster.from_url(
            settings.REDIS_URL,
            **kwargs,
        )
    else:
        client = aioredis.Redis.from_url(settings.REDIS_URL, **kwargs)

    return AsyncRedisClient(client)
