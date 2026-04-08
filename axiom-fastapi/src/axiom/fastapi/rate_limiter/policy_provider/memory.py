"""axiom.fastapi.rate_limiter.policy_provider.memory — Mutable in-memory PolicyProvider."""

import asyncio

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy

__all__ = [
    "InMemoryPolicyProvider",
]


class InMemoryPolicyProvider:
    """Mutable in-memory policy provider for dev, test, and hot-reload scenarios.

    Policies can be replaced at runtime via ``set_policies()`` without restarting
    the application. All reads and writes are protected by an ``asyncio.Lock``.

    For production use, prefer ``RedisPolicyProvider`` wrapped in
    ``CachedPolicyProvider`` for cross-process consistency.
    """

    def __init__(
        self,
        policies: list[RateLimitPolicy | PolicyGroup] | None = None,
    ) -> None:
        """Initialize with an optional starting policy list.

        Args:
            policies: Initial policies. Defaults to empty list.
        """
        self._policies: list[RateLimitPolicy | PolicyGroup] = list(policies or [])
        self._lock = asyncio.Lock()

    async def set_policies(
        self,
        policies: list[RateLimitPolicy | PolicyGroup],
    ) -> None:
        """Replace the current policy list atomically.

        Args:
            policies: New policy list to activate immediately.
        """
        async with self._lock:
            self._policies = list(policies)

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Return a snapshot of the current policy list.

        Args:
            context: Ignored — all requests receive the same policy list.

        Returns:
            A copy of the current policy list.
        """
        async with self._lock:
            return list(self._policies)
