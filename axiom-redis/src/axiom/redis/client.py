"""axiom.redis.client — Redis client factory and wrapper."""

from __future__ import annotations

from typing import Any

try:
    from redis.asyncio import Redis
except ImportError as e:
    raise ImportError("redis is required: uv add redis") from e


class RedisClient:
    """Thin wrapper around async Redis client."""

    def __init__(self, client: Redis) -> None:
        """Wrap the given async Redis client."""
        self._client = client

    @property
    def raw(self) -> Redis:
        """Access the underlying Redis client."""
        return self._client

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._client.aclose()


def create_redis_client(
    url: str = "redis://localhost:6379",
    **kwargs: Any,
) -> RedisClient:
    """Create a Redis client from a URL."""
    return RedisClient(Redis.from_url(url, **kwargs))
