"""axiom.fastapi.rate_limiter.middleware — ASGI middleware for global rate limiting."""

import math
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from axiom.core.exceptions.base import ErrorDetail
from axiom.core.logger import get_logger
from axiom.fastapi.rate_limiter.service import RateLimiterService

__all__ = [
    "RateLimitMiddleware",
]

logger = get_logger("axiom.fastapi.rate_limiter.middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that enforces rate limits on every inbound request.

    Add to a FastAPI / Starlette app::

        app.add_middleware(RateLimitMiddleware, service=service, exempt_paths={"/health"})

    On blocked requests, responds with HTTP 429 and the standard ``ErrorDetail``
    body plus rate-limit headers::

        X-RateLimit-Limit: 100
        X-RateLimit-Remaining: 0
        X-RateLimit-Reset: 1712661600
        Retry-After: 42
    """

    def __init__(
        self,
        app: object,
        service: RateLimiterService,
        exempt_paths: set[str] | None = None,
    ) -> None:
        """Initialize the middleware.

        Args:
            app: ASGI application.
            service: Configured ``RateLimiterService`` instance.
            exempt_paths: Path strings that bypass rate limiting (e.g. ``'/health'``).
        """
        super().__init__(app)  # type: ignore[arg-type]
        self._service = service
        self._exempt_paths: set[str] = exempt_paths or set()

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Evaluate rate limits before forwarding the request.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            HTTP 429 JSON response if rate limit exceeded, otherwise upstream response.
        """
        path = request.url.path
        if path in self._exempt_paths:
            logger.debug("rate_limit.exempt", path=path)
            return await call_next(request)  # type: ignore[operator]

        results = await self._service.check_request(request)
        blocked = next((r for r in results if not r.allowed), None)

        if blocked is not None:
            reset_ts = int(blocked.reset_at.timestamp())
            retry_after = max(0, math.ceil(reset_ts - time.time()))
            logger.warning(
                "rate_limit.blocked",
                path=path,
                key=blocked.key,
                limit=blocked.limit,
            )
            body = ErrorDetail(
                code="rate_limit_exceeded",
                message="Too many requests",
                details={
                    "limit": str(blocked.limit),
                    "remaining": blocked.remaining,
                    "reset_at": blocked.reset_at.isoformat(),
                },
            ).model_dump()
            return JSONResponse(
                status_code=429,
                content=body,
                headers={
                    "X-RateLimit-Limit": str(blocked.limit),
                    "X-RateLimit-Remaining": str(blocked.remaining),
                    "X-RateLimit-Reset": str(reset_ts),
                    "Retry-After": str(retry_after),
                },
            )

        response: Response = await call_next(request)  # type: ignore[operator]

        if results:
            first = results[0]
            reset_ts = int(first.reset_at.timestamp())
            response.headers["X-RateLimit-Limit"] = str(first.limit)
            response.headers["X-RateLimit-Remaining"] = str(first.remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_ts)

        logger.debug("rate_limit.allowed", path=path)
        return response
