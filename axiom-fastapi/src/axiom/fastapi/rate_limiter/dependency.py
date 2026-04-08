"""axiom.fastapi.rate_limiter.dependency — FastAPI Depends() factory for per-endpoint rate limiting."""

import math
import time
from collections.abc import Callable

from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.exception import RateLimitExceededError
from axiom.fastapi.rate_limiter.key_builder.base import KeyBuilder
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from fastapi import Request, Response
from fastapi.exceptions import HTTPException

__all__ = [
    "rate_limit",
]


def rate_limit(
    limit: str,
    scope: RateLimitScope = RateLimitScope.IP,
    algorithm: Algorithm = Algorithm.FIXED_WINDOW,
    key_builder: KeyBuilder | None = None,
) -> Callable[..., object]:
    """Return a FastAPI dependency that enforces a rate limit on a single endpoint.

    The returned callable is compatible with ``Depends()``::

        @router.get("/items")
        async def list_items(_: None = Depends(rate_limit("100/min"))): ...

    The ``RateLimiterService`` is resolved from ``request.app.state.rate_limiter``
    via ``AppStateManager``. Raises HTTP 500 if the service is not configured.

    Sets response headers on allowed requests:
    ``X-RateLimit-Limit``, ``X-RateLimit-Remaining``, ``X-RateLimit-Reset``,
    ``Retry-After``.

    Args:
        limit: Rate limit string in ``limits`` format, e.g. ``'100/min'``.
        scope: The scope at which the limit applies. Defaults to ``IP``.
        algorithm: Rate limiting algorithm. Defaults to ``FIXED_WINDOW``.
        key_builder: Optional custom key builder. Defaults to ``IPKeyBuilder``.

    Returns:
        An async callable compatible with FastAPI ``Depends()``.

    Raises:
        HTTPException(500): If ``RateLimiterService`` is not attached to ``app.state``.
        RateLimitExceededError: When the rate limit is exceeded (caught by exception handler).
    """
    _key_builder: KeyBuilder = key_builder or IPKeyBuilder()

    async def _check(request: Request, response: Response) -> RateLimitResult:
        from axiom.fastapi.app.state import AppStateManager
        from axiom.fastapi.rate_limiter.service import RateLimiterService

        try:
            service = AppStateManager(request.app).get("rate_limiter", RateLimiterService)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Rate limiter service is not configured. "
                    "Call rate_limiter_lifespan() or setup_rate_limiter() during app startup."
                ),
            ) from exc

        policy_name = f"{request.method}:{request.url.path}:{limit}"
        policy = RateLimitPolicy(
            limit=limit,
            scope=scope,
            algorithm=algorithm,
            name=policy_name,
        )

        key = await _key_builder.build_key(request, policy)
        result = await service._backend.check(key, policy)  # noqa: SLF001

        reset_ts = int(result.reset_at.timestamp())
        retry_after = max(0, math.ceil(reset_ts - time.time()))
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_ts)
        response.headers["Retry-After"] = str(retry_after)

        if not result.allowed:
            raise RateLimitExceededError(
                f"Rate limit exceeded: {limit}",
                details={
                    "key": key,
                    "limit": str(result.limit),
                    "remaining": result.remaining,
                    "reset_at": result.reset_at.isoformat(),
                },
            )

        return result

    return _check
