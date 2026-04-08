"""axiom.fastapi.rate_limiter.core.scope — Rate limiting scope enum."""

from enum import Enum

__all__ = [
    "RateLimitScope",
]


class RateLimitScope(str, Enum):
    """Scope at which rate limiting is applied."""

    API_KEY = "api_key"
    GLOBAL = "global"
    IP = "ip"
    ROUTE = "route"
    TENANT = "tenant"
    USER = "user"
