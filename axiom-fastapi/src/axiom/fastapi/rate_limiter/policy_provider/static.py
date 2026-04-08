"""axiom.fastapi.rate_limiter.policy_provider.static — Static in-memory PolicyProvider."""

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy

__all__ = [
    "StaticPolicyProvider",
]


class StaticPolicyProvider:
    """Policy provider backed by a fixed, immutable list.

    Wraps a ``list[RateLimitPolicy | PolicyGroup]`` so that ``RateLimiterService``
    always interacts with a uniform ``PolicyProvider`` interface regardless of
    whether the caller passed a list or a dynamic provider.

    Use ``InMemoryPolicyProvider`` if you need runtime updates.
    """

    def __init__(self, policies: list[RateLimitPolicy | PolicyGroup]) -> None:
        """Initialize with a fixed policy list.

        Args:
            policies: Ordered list of policies returned on every request.
        """
        self._policies = list(policies)

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Return the fixed policy list regardless of context.

        Args:
            context: Ignored — all requests receive the same policy list.

        Returns:
            The immutable policy list supplied at construction.
        """
        return self._policies
