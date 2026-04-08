"""Unit tests for axiom.fastapi.rate_limiter.service.RateLimiterService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.exception import RateLimitBackendError
from axiom.fastapi.rate_limiter.service import RateLimiterService


def _make_policy(name: str = "test") -> RateLimitPolicy:
    return RateLimitPolicy(limit="10/minute", scope=RateLimitScope.IP, name=name)


def _make_result(allowed: bool = True, key: str = "rl:ip:127.0.0.1") -> RateLimitResult:
    return RateLimitResult(
        allowed=allowed,
        key=key,
        limit=10,
        policy_name="test",
        remaining=9 if allowed else 0,
        reset_at=datetime.now(tz=timezone.utc),
    )


def _make_request() -> MagicMock:
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


async def test_fail_open_on_backend_error_returns_allowed_result() -> None:
    backend = MagicMock()
    backend.check = AsyncMock(side_effect=RateLimitBackendError("Redis down"))
    key_builder = MagicMock()
    key_builder.build_key = AsyncMock(return_value="rl:ip:127.0.0.1")

    service = RateLimiterService(
        backend=backend,
        policies=[_make_policy()],
        key_builder=key_builder,
        failure_strategy=FailureStrategy.FAIL_OPEN,
    )
    results = await service.check_request(_make_request())
    assert len(results) == 1
    assert results[0].allowed is True


async def test_fail_closed_on_backend_error_re_raises() -> None:
    backend = MagicMock()
    backend.check = AsyncMock(side_effect=RateLimitBackendError("Redis down"))
    key_builder = MagicMock()
    key_builder.build_key = AsyncMock(return_value="rl:ip:127.0.0.1")

    service = RateLimiterService(
        backend=backend,
        policies=[_make_policy()],
        key_builder=key_builder,
        failure_strategy=FailureStrategy.FAIL_CLOSED,
    )
    with pytest.raises(RateLimitBackendError):
        await service.check_request(_make_request())


async def test_short_circuit_on_first_blocked_policy() -> None:
    backend = MagicMock()
    blocked_result = _make_result(allowed=False)
    allowed_result = _make_result(allowed=True)
    backend.check = AsyncMock(side_effect=[blocked_result, allowed_result])
    key_builder = MagicMock()
    key_builder.build_key = AsyncMock(return_value="rl:ip:127.0.0.1")

    policy1 = _make_policy("p1")
    policy2 = _make_policy("p2")

    service = RateLimiterService(
        backend=backend,
        policies=[policy1, policy2],
        key_builder=key_builder,
    )
    results = await service.check_request(_make_request())
    # Only first policy evaluated — short-circuit after block
    assert len(results) == 1
    assert results[0].allowed is False
    assert backend.check.call_count == 1


async def test_all_policies_evaluated_when_all_allowed() -> None:
    backend = MagicMock()
    backend.check = AsyncMock(return_value=_make_result(allowed=True))
    key_builder = MagicMock()
    key_builder.build_key = AsyncMock(return_value="rl:ip:127.0.0.1")

    service = RateLimiterService(
        backend=backend,
        policies=[_make_policy("p1"), _make_policy("p2"), _make_policy("p3")],
        key_builder=key_builder,
    )
    results = await service.check_request(_make_request())
    assert len(results) == 3
    assert all(r.allowed for r in results)
