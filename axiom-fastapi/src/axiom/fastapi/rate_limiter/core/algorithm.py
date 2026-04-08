"""axiom.fastapi.rate_limiter.core.algorithm — Rate limiting algorithm and failure strategy enums."""

from enum import Enum

__all__ = [
    "Algorithm",
    "FailureStrategy",
]


class Algorithm(str, Enum):
    """Supported rate limiting algorithms."""

    FIXED_WINDOW = "fixed_window"
    MOVING_WINDOW = "moving_window"
    SLIDING_WINDOW = "sliding_window"


class FailureStrategy(str, Enum):
    """Strategy when rate limit backend is unavailable."""

    FAIL_CLOSED = "fail_closed"
    FAIL_OPEN = "fail_open"
