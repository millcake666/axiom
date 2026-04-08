# mypy: disable-error-code="misc"
"""axiom.fastapi.rate_limiter.backend.redis — Redis-backed rate limit backend for production."""

from datetime import datetime, timezone

from limits import parse as limits_parse
from limits.storage import RedisStorage
from limits.strategies import (
    FixedWindowElasticExpiryRateLimiter,
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
)

from axiom.fastapi.rate_limiter.backend.base import RateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.exception import RateLimitBackendError

__all__ = [
    "RedisRateLimitBackend",
]


class RedisRateLimitBackend(RateLimitBackend):
    """Redis-backed rate limit backend using limits.storage.RedisStorage.

    Uses atomic Lua scripts provided by the limits library.
    The AsyncRedisClient is used only for health checks and shutdown;
    limits.storage.RedisStorage manages its own connection pool.
    """

    def __init__(self, redis_url: str, async_redis_client: object) -> None:
        """Initialize with Redis URL and an AsyncRedisClient for management ops.

        Args:
            redis_url: Redis connection URL (e.g. 'redis://localhost:6379').
            async_redis_client: AsyncRedisClient instance used for health checks.
        """
        self._async_client = async_redis_client
        self._storage = RedisStorage(redis_url)
        self._fixed = FixedWindowRateLimiter(self._storage)
        self._elastic = FixedWindowElasticExpiryRateLimiter(self._storage)
        self._moving = MovingWindowRateLimiter(self._storage)

    def _get_limiter(
        self,
        algorithm: Algorithm,
    ) -> FixedWindowRateLimiter | FixedWindowElasticExpiryRateLimiter | MovingWindowRateLimiter:
        if algorithm == Algorithm.SLIDING_WINDOW:
            return self._elastic
        if algorithm == Algorithm.MOVING_WINDOW:
            return self._moving
        return self._fixed

    async def check(self, key: str, policy: RateLimitPolicy) -> RateLimitResult:
        """Check and increment the rate limit counter for a key."""
        try:
            item = limits_parse(policy.limit)
            limiter = self._get_limiter(policy.algorithm)
            allowed = limiter.hit(item, key)
            stats = limiter.get_window_stats(item, key)
            reset_at = datetime.fromtimestamp(stats.reset_time, tz=timezone.utc)
            return RateLimitResult(
                allowed=allowed,
                key=key,
                limit=item.amount,
                policy_name=policy.name,
                remaining=stats.remaining,
                reset_at=reset_at,
            )
        except Exception as exc:
            raise RateLimitBackendError(f"Redis rate limit check failed: {exc}") from exc

    async def get_remaining(self, key: str, policy: RateLimitPolicy) -> int:
        """Return remaining requests without incrementing counter."""
        try:
            item = limits_parse(policy.limit)
            limiter = self._get_limiter(policy.algorithm)
            stats = limiter.get_window_stats(item, key)
            return stats.remaining
        except Exception as exc:
            raise RateLimitBackendError(f"Redis get_remaining failed: {exc}") from exc

    async def reset(self, key: str) -> None:
        """Reset all rate limit counters for a key by scanning for matching Redis keys."""
        try:
            pattern = f"*/{key}/*"
            keys = [k async for k in self._async_client.scan_iter(pattern)]  # type: ignore[attr-defined]
            if keys:
                await self._async_client.delete(*keys)  # type: ignore[attr-defined]
        except Exception as exc:
            raise RateLimitBackendError(f"Redis reset failed for key '{key}': {exc}") from exc

    async def startup(self) -> None:
        """Validate Redis connectivity via health check."""
        try:
            await self._async_client.exists("ping_probe")  # type: ignore[attr-defined]
        except Exception as exc:
            raise RateLimitBackendError(
                f"Redis backend startup failed: {exc}",
            ) from exc

    async def shutdown(self) -> None:
        """Close the Redis connection."""
        await self._async_client.close()  # type: ignore[attr-defined]
