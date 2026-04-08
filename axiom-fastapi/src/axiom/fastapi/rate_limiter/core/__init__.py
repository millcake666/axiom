"""axiom.fastapi.rate_limiter.core — Core domain types for rate limiting."""

from axiom.fastapi.rate_limiter.core.algorithm import Algorithm, FailureStrategy
from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import (
    GlobalPolicy,
    IPPolicy,
    PolicyGroup,
    RateLimitPolicy,
    RoutePolicy,
    UserPolicy,
)
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope

__all__ = [
    "Algorithm",
    "FailureStrategy",
    "GlobalPolicy",
    "IPPolicy",
    "PolicyGroup",
    "RateLimitPolicy",
    "RateLimitResult",
    "RateLimitScope",
    "RequestContext",
    "RoutePolicy",
    "UserPolicy",
]
