"""Unit tests for axiom.fastapi.rate_limiter.core.policy."""

import pytest

from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import GlobalPolicy, IPPolicy, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope


def _make_policy(**kwargs: object) -> RateLimitPolicy:
    defaults = {"limit": "10/minute", "scope": RateLimitScope.IP}
    defaults.update(kwargs)  # type: ignore[arg-type]
    return RateLimitPolicy(**defaults)  # type: ignore[arg-type]


def test_valid_limit_string_parses_without_error() -> None:
    policy = _make_policy(limit="100/minute")
    assert policy.limit == "100/minute"


def test_invalid_limit_string_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Invalid rate limit string"):
        _make_policy(limit="not-a-valid-limit")


def test_default_algorithm_is_fixed_window() -> None:
    policy = _make_policy()
    assert policy.algorithm == Algorithm.FIXED_WINDOW


def test_global_policy_has_correct_default_scope() -> None:
    policy = GlobalPolicy(limit="50/second")
    assert policy.scope == RateLimitScope.GLOBAL


def test_ip_policy_has_correct_default_scope() -> None:
    policy = IPPolicy(limit="50/second")
    assert policy.scope == RateLimitScope.IP


def test_policy_key_prefix_default() -> None:
    policy = _make_policy()
    assert policy.key_prefix == "rl"


def test_policy_name_default_is_empty_string() -> None:
    policy = _make_policy()
    assert policy.name == ""
