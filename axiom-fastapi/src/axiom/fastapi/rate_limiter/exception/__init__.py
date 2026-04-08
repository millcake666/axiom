# mypy: disable-error-code="misc"
"""axiom.fastapi.rate_limiter.exception — Exceptions for the axiom.fastapi.rate_limiter package."""

from axiom.core.exceptions.base import BaseError

__all__ = [
    "RateLimitBackendError",
    "RateLimitError",
    "RateLimitExceededError",
]


class RateLimitError(BaseError):
    """Base exception for rate limiting errors."""

    code = "rate_limit_error"
    status_code = 500


class RateLimitBackendError(RateLimitError):
    """Rate limit backend is unavailable or failed."""

    code = "rate_limit_backend_error"
    status_code = 503


class RateLimitExceededError(RateLimitError):
    """Rate limit has been exceeded."""

    code = "rate_limit_exceeded"
    status_code = 429
