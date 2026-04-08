"""axiom.fastapi.rate_limiter.core.policy — Rate limit policy definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from limits import parse as limits_parse

from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope

__all__ = [
    "GlobalPolicy",
    "IPPolicy",
    "PolicyGroup",
    "RateLimitPolicy",
    "RoutePolicy",
    "UserPolicy",
]


@dataclass
class RateLimitPolicy:
    """Composable rate limit policy definition.

    Validates the limit string at construction time via limits.parse().
    """

    limit: str
    scope: RateLimitScope
    algorithm: Algorithm = field(default=Algorithm.FIXED_WINDOW)
    key_prefix: str = field(default="rl")
    name: str = field(default="")

    def __post_init__(self) -> None:
        """Validate limit string via limits.parse()."""
        try:
            limits_parse(self.limit)
        except Exception as exc:
            raise ValueError(
                f"Invalid rate limit string '{self.limit}'. "
                "Expected format: '<count>/<period>' (e.g. '100/minute', '10/second').",
            ) from exc


@dataclass
class PolicyGroup:
    """Composite policy container supporting AND / OR evaluation modes.

    AND (default): all member policies must pass (sequential, short-circuits on first block).
    OR: at least one member policy must pass (evaluates all, allows if any passes).

    Groups can be nested recursively.
    """

    policies: list[RateLimitPolicy | PolicyGroup] = field(default_factory=list)
    mode: Literal["AND", "OR"] = "AND"
    name: str = ""


@dataclass
class GlobalPolicy(RateLimitPolicy):
    """Rate limit policy applied globally across all requests."""

    scope: RateLimitScope = field(default=RateLimitScope.GLOBAL)


@dataclass
class IPPolicy(RateLimitPolicy):
    """Rate limit policy applied per client IP address."""

    scope: RateLimitScope = field(default=RateLimitScope.IP)


@dataclass
class RoutePolicy(RateLimitPolicy):
    """Rate limit policy applied per route."""

    scope: RateLimitScope = field(default=RateLimitScope.ROUTE)


@dataclass
class UserPolicy(RateLimitPolicy):
    """Rate limit policy applied per authenticated user."""

    scope: RateLimitScope = field(default=RateLimitScope.USER)
