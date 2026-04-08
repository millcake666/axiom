# mypy: disable-error-code="misc"
"""axiom.fastapi.rate_limiter.backend.memory — In-memory rate limit backend for dev/test.

Not suitable for production (single-process only). Use RedisRateLimitBackend for
distributed deployments.
"""

import asyncio
from datetime import datetime, timezone

from limits import parse as limits_parse
from limits.storage import MemoryStorage
from limits.strategies import (
    FixedWindowElasticExpiryRateLimiter,
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
)

from axiom.fastapi.rate_limiter.backend.base import RateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult

__all__ = [
    "InMemoryRateLimitBackend",
]


class InMemoryRateLimitBackend(RateLimitBackend):
    """In-memory rate limit backend using limits.storage.MemoryStorage.

    Suitable for development and testing. Single-process only — does not share
    state across multiple workers or instances.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage and algorithm instances."""
        self._storage = MemoryStorage()
        self._fixed = FixedWindowRateLimiter(self._storage)
        self._elastic = FixedWindowElasticExpiryRateLimiter(self._storage)
        self._moving = MovingWindowRateLimiter(self._storage)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

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
        item = limits_parse(policy.limit)
        limiter = self._get_limiter(policy.algorithm)
        async with self._get_lock(key):
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

    async def get_remaining(self, key: str, policy: RateLimitPolicy) -> int:
        """Return remaining requests without incrementing counter."""
        item = limits_parse(policy.limit)
        limiter = self._get_limiter(policy.algorithm)
        stats = limiter.get_window_stats(item, key)
        return stats.remaining

    async def reset(self, key: str) -> None:
        """Reset all algorithm counters for a key.

        Clears all storage entries that contain the given key segment.
        """
        keys_to_clear = [
            k
            for k in list(self._storage.storage.keys())
            if f"/{key}/" in k or k.endswith(f"/{key}")
        ]
        for storage_key in keys_to_clear:
            self._storage.clear(storage_key)

    async def startup(self) -> None:
        """No-op for in-memory backend."""

    async def shutdown(self) -> None:
        """No-op for in-memory backend."""
