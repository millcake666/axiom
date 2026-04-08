"""axiom.fastapi.rate_limiter.key_builder.ip — IP-based key extraction."""

from starlette.requests import Request

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy

__all__ = [
    "IPKeyBuilder",
]


class IPKeyBuilder:
    """Extracts the client IP address as the rate limit key."""

    async def build_key(self, request: Request, policy: RateLimitPolicy) -> str:
        """Build key from client IP address.

        Uses X-Forwarded-For header if present, falls back to request.client.host.

        Args:
            request: Incoming HTTP request.
            policy: The rate limit policy being evaluated.

        Returns:
            Key in the format '{policy.key_prefix}:ip:{ip}'.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        elif request.client:
            ip = request.client.host
        else:
            ip = "unknown"
        return f"{policy.key_prefix}:ip:{ip}"
