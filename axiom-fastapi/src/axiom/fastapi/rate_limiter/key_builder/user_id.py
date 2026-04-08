"""axiom.fastapi.rate_limiter.key_builder.user_id — User ID-based key extraction."""

from starlette.requests import Request

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.exception import RateLimitError

__all__ = [
    "UserIdKeyBuilder",
]


class UserIdKeyBuilder:
    """Extracts the authenticated user ID from request state as the rate limit key."""

    def __init__(self, state_attr: str = "user_id") -> None:
        """Initialize with the request state attribute name.

        Args:
            state_attr: Name of the attribute on request.state containing the user ID.
        """
        self._state_attr = state_attr

    async def build_key(self, request: Request, policy: RateLimitPolicy) -> str:
        """Build key from request.state user ID.

        Args:
            request: Incoming HTTP request.
            policy: The rate limit policy being evaluated.

        Returns:
            Key in the format '{policy.key_prefix}:user:{user_id}'.

        Raises:
            RateLimitError: If user_id is not present on request.state.
        """
        user_id = getattr(request.state, self._state_attr, None)
        if user_id is None:
            raise RateLimitError(
                f"User ID not found on request.state.{self._state_attr}. "
                "Ensure authentication middleware runs before rate limiting.",
            )
        return f"{policy.key_prefix}:user:{user_id}"
