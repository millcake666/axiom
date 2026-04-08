"""axiom.fastapi.rate_limiter.core.result — Rate limit check result dataclass."""

from dataclasses import dataclass
from datetime import datetime

__all__ = [
    "RateLimitResult",
]


@dataclass
class RateLimitResult:
    """Result of a rate limit check operation."""

    allowed: bool
    key: str
    limit: int
    policy_name: str
    remaining: int
    reset_at: datetime
