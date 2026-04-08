"""axiom.fastapi.rate_limiter.key_builder.base — KeyBuilder Protocol definition."""

from typing import Protocol, runtime_checkable

from starlette.requests import Request

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy

__all__ = [
    "KeyBuilder",
]


@runtime_checkable
class KeyBuilder(Protocol):
    """Protocol for building rate limit storage keys from requests."""

    async def build_key(self, request: Request, policy: RateLimitPolicy) -> str:
        """Build a rate limit key from request and policy.

        Args:
            request: Incoming HTTP request.
            policy: The rate limit policy being evaluated.

        Returns:
            A unique string key for this request + policy combination.
        """
        ...
