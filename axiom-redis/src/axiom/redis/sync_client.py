"""axiom.redis.sync_client — Sync Redis client."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import redis
from axiom.redis.exception import RedisOperationError
from axiom.redis.settings import RedisSettings


class SyncRedisClient:
    """Synchronous Redis client wrapping redis.Redis."""

    def __init__(self, client: redis.Redis | redis.RedisCluster) -> None:
        """Initialize with an existing sync Redis client."""
        self._client = client

    @property
    def raw(self) -> redis.Redis | redis.RedisCluster:
        """Return the underlying sync Redis client."""
        return self._client

    def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if key does not exist."""
        try:
            return self._client.get(key)
        except Exception as exc:
            raise RedisOperationError(f"GET failed for key '{key}'") from exc

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a key to value with optional TTL in seconds."""
        try:
            if ttl is not None:
                self._client.set(key, value, ex=ttl)
            else:
                self._client.set(key, value)
        except Exception as exc:
            raise RedisOperationError(f"SET failed for key '{key}'") from exc

    def delete(self, *keys: str) -> None:
        """Delete one or more keys."""
        try:
            if keys:
                self._client.delete(*keys)
        except Exception as exc:
            raise RedisOperationError(f"DELETE failed for keys {keys}") from exc

    def exists(self, key: str) -> bool:
        """Return True if the key exists."""
        try:
            result = self._client.exists(key)
            return bool(result)
        except Exception as exc:
            raise RedisOperationError(f"EXISTS failed for key '{key}'") from exc

    def expire(self, key: str, seconds: int) -> None:
        """Set expiry on a key."""
        try:
            self._client.expire(key, seconds)
        except Exception as exc:
            raise RedisOperationError(f"EXPIRE failed for key '{key}'") from exc

    def ttl(self, key: str) -> int:
        """Return TTL in seconds for a key. Returns -2 if key doesn't exist, -1 if no TTL."""
        try:
            result = self._client.ttl(key)
            return cast(int, result)
        except Exception as exc:
            raise RedisOperationError(f"TTL failed for key '{key}'") from exc

    def scan_iter(self, pattern: str) -> Iterator[str]:
        """Generator yielding keys matching the given pattern."""
        try:
            for key in self._client.scan_iter(match=pattern):
                if isinstance(key, bytes):
                    yield key.decode()
                else:
                    yield str(key)
        except Exception as exc:
            raise RedisOperationError(f"SCAN failed for pattern '{pattern}'") from exc

    def flushall(self) -> None:
        """Flush all keys from the current database."""
        try:
            self._client.flushall()
        except Exception as exc:
            raise RedisOperationError("FLUSHALL failed") from exc

    def close(self) -> None:
        """Close the Redis connection."""
        try:
            self._client.close()
        except Exception as exc:
            raise RedisOperationError("CLOSE failed") from exc


def create_sync_redis_client(settings: RedisSettings) -> SyncRedisClient:
    """Create a SyncRedisClient from settings."""
    kwargs: dict[str, Any] = {
        "decode_responses": settings.REDIS_DECODE_RESPONSES,
    }
    if settings.REDIS_MAX_CONNECTIONS is not None:
        kwargs["max_connections"] = settings.REDIS_MAX_CONNECTIONS
    if settings.REDIS_SOCKET_TIMEOUT is not None:
        kwargs["socket_timeout"] = settings.REDIS_SOCKET_TIMEOUT

    if settings.REDIS_USE_CLUSTER:
        client: redis.Redis | redis.RedisCluster = redis.RedisCluster.from_url(
            settings.REDIS_URL,
            **kwargs,
        )
    else:
        client = redis.Redis.from_url(settings.REDIS_URL, **kwargs)

    return SyncRedisClient(client)
