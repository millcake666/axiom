"""axiom.fastapi.rate_limiter.policy_provider.base — PolicyProvider Protocol."""

from typing import Protocol, runtime_checkable

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy

__all__ = [
    "PolicyProvider",
]


@runtime_checkable
class PolicyProvider(Protocol):
    """Protocol for rate limit policy sources.

    Implementations return a list of policies (or policy groups) to apply for
    a given request context. Consumers can use any of the built-in providers
    or supply a custom implementation:

    - ``StaticPolicyProvider`` — fixed list, suitable for service init from config
    - ``InMemoryPolicyProvider`` — mutable, suitable for dev / test hot-reload
    - ``RedisPolicyProvider`` — Redis-backed, versioned, env-namespaced
    - ``PostgresPolicyProvider`` — SQL-backed via repository abstraction
    - ``CachedPolicyProvider`` — wraps any provider with TTL-based caching
    """

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Return the ordered list of policies to evaluate for a request.

        Args:
            context: Lightweight request context (path, method, client_ip, user_id, tenant_id).

        Returns:
            Ordered list of RateLimitPolicy or PolicyGroup items.
            Empty list means no rate limiting is applied.
        """
        ...
