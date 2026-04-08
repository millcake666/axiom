"""axiom.fastapi.rate_limiter — Request rate limiting and throttling."""

__version__ = "0.1.0"

from axiom.fastapi.rate_limiter.backend.base import RateLimitBackend
from axiom.fastapi.rate_limiter.backend.memory import InMemoryRateLimitBackend
from axiom.fastapi.rate_limiter.backend.redis import RedisRateLimitBackend
from axiom.fastapi.rate_limiter.config import RateLimitConfig, RateLimitSettings
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
from axiom.fastapi.rate_limiter.dependency import rate_limit
from axiom.fastapi.rate_limiter.exception import (
    RateLimitBackendError,
    RateLimitError,
    RateLimitExceededError,
)
from axiom.fastapi.rate_limiter.key_builder.api_key import ApiKeyKeyBuilder
from axiom.fastapi.rate_limiter.key_builder.base import KeyBuilder
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from axiom.fastapi.rate_limiter.key_builder.user_id import UserIdKeyBuilder
from axiom.fastapi.rate_limiter.middleware import RateLimitMiddleware
from axiom.fastapi.rate_limiter.policy_provider.base import PolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.cached import CachedPolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.memory import InMemoryPolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.postgres import (
    PolicyRepository,
    PostgresPolicyProvider,
)
from axiom.fastapi.rate_limiter.policy_provider.redis import RedisPolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.static import StaticPolicyProvider
from axiom.fastapi.rate_limiter.service import (
    RateLimiterService,
    rate_limiter_lifespan,
    setup_rate_limiter,
)

__all__ = [
    "Algorithm",
    "ApiKeyKeyBuilder",
    "CachedPolicyProvider",
    "FailureStrategy",
    "GlobalPolicy",
    "IPKeyBuilder",
    "IPPolicy",
    "InMemoryPolicyProvider",
    "InMemoryRateLimitBackend",
    "KeyBuilder",
    "PolicyGroup",
    "PolicyProvider",
    "PolicyRepository",
    "PostgresPolicyProvider",
    "RateLimitBackend",
    "RateLimitBackendError",
    "RateLimitConfig",
    "RateLimitError",
    "RateLimitExceededError",
    "RateLimitMiddleware",
    "RateLimitPolicy",
    "RateLimitResult",
    "RateLimitScope",
    "RateLimitSettings",
    "RateLimiterService",
    "RedisPolicyProvider",
    "RedisRateLimitBackend",
    "RequestContext",
    "RoutePolicy",
    "StaticPolicyProvider",
    "UserIdKeyBuilder",
    "UserPolicy",
    "rate_limit",
    "rate_limiter_lifespan",
    "setup_rate_limiter",
]
