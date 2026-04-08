"""axiom.fastapi.rate_limiter.key_builder.api_key — API key-based key extraction."""

import hashlib

from starlette.requests import Request

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy

__all__ = [
    "ApiKeyKeyBuilder",
]


class ApiKeyKeyBuilder:
    """Extracts and hashes an API key header as the rate limit key."""

    def __init__(self, header_name: str = "X-API-Key") -> None:
        """Initialize with the header name to read the API key from.

        Args:
            header_name: HTTP header containing the API key. Defaults to 'X-API-Key'.
        """
        self._header_name = header_name

    async def build_key(self, request: Request, policy: RateLimitPolicy) -> str:
        """Build key from hashed API key header value.

        Args:
            request: Incoming HTTP request.
            policy: The rate limit policy being evaluated.

        Returns:
            Key in the format '{policy.key_prefix}:apikey:{hashed_key}'.
            Uses SHA256 first 16 hex chars as the hash.
            Returns 'unknown' if header is absent.
        """
        api_key = request.headers.get(self._header_name, "")
        hashed = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return f"{policy.key_prefix}:apikey:{hashed}"
