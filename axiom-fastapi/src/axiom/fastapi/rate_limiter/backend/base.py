"""axiom.fastapi.rate_limiter.backend.base — Abstract base class for rate limit backends."""

from abc import ABC, abstractmethod

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult

__all__ = [
    "RateLimitBackend",
]


class RateLimitBackend(ABC):
    """Abstract base class for rate limit storage backends."""

    @abstractmethod
    async def check(self, key: str, policy: RateLimitPolicy) -> RateLimitResult:
        """Check and increment the rate limit counter for a key.

        Args:
            key: The rate limit storage key.
            policy: The rate limit policy to apply.

        Returns:
            RateLimitResult with allowed status and counter details.
        """

    @abstractmethod
    async def get_remaining(self, key: str, policy: RateLimitPolicy) -> int:
        """Return the number of remaining requests for a key.

        Args:
            key: The rate limit storage key.
            policy: The rate limit policy to evaluate.

        Returns:
            Number of remaining requests in the current window.
        """

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset all counters for a key.

        Args:
            key: The rate limit storage key to clear.
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the backend and release resources."""

    @abstractmethod
    async def startup(self) -> None:
        """Initialize the backend and verify connectivity."""
