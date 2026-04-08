"""axiom.fastapi.rate_limiter.policy_provider.cached — TTL-cached PolicyProvider wrapper."""

import time

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.policy_provider.base import PolicyProvider

__all__ = [
    "CachedPolicyProvider",
]


class CachedPolicyProvider:
    """Wraps any PolicyProvider with TTL-based in-process caching.

    Prevents a round-trip to slow backends (Postgres, Redis) on every request.
    After the TTL expires, the next call fetches fresh policies from the inner
    provider and resets the TTL.

    If the inner provider raises after the cache has been warmed up, the last
    known policies are served as a fallback (fail-open for configuration reads).
    If the provider fails on the very first call (cold cache), the error propagates.

    Typical production setup::

        provider = CachedPolicyProvider(
            PostgresPolicyProvider(repo),
            ttl=30.0,
        )

    Manual invalidation (e.g. after an admin policy update)::

        provider.invalidate()
    """

    def __init__(self, inner: PolicyProvider, ttl: float = 5.0) -> None:
        """Initialize the caching wrapper.

        Args:
            inner: Delegate PolicyProvider to fetch policies from.
            ttl: Cache TTL in seconds. Defaults to ``5.0``.
        """
        self._inner = inner
        self._ttl = ttl
        self._cached: list[RateLimitPolicy | PolicyGroup] | None = None
        self._expires_at: float = 0.0

    def invalidate(self) -> None:
        """Manually invalidate the cache, forcing a reload on the next request."""
        self._cached = None
        self._expires_at = 0.0

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Return cached policies, refreshing from inner provider if TTL expired.

        Args:
            context: Forwarded to the inner provider on a cache miss.

        Returns:
            Policy list from cache or freshly fetched from the inner provider.

        Raises:
            Exception: Propagated from inner provider only when the cache is cold.
        """
        now = time.monotonic()
        if self._cached is not None and now < self._expires_at:
            return self._cached

        try:
            policies = await self._inner.get_policies(context)
            self._cached = policies
            self._expires_at = now + self._ttl
            return self._cached
        except Exception:
            if self._cached is not None:
                # Serve stale cache on provider failure (fail-open for config reads)
                return self._cached
            raise
