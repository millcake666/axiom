"""Unit tests for PolicyGroup AND/OR evaluation in RateLimiterService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.policy import IPPolicy, PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.service import RateLimiterService


def _make_policy(name: str = "p") -> RateLimitPolicy:
    return RateLimitPolicy(limit="10/minute", scope=RateLimitScope.IP, name=name)


def _make_result(allowed: bool, name: str = "p") -> RateLimitResult:
    return RateLimitResult(
        allowed=allowed,
        key="k",
        limit=10,
        policy_name=name,
        remaining=9 if allowed else 0,
        reset_at=datetime.now(tz=timezone.utc),
    )


def _make_request() -> MagicMock:
    r = MagicMock()
    r.headers = {}
    r.client = MagicMock()
    r.client.host = "127.0.0.1"
    r.state = MagicMock(spec=[])  # spec=[] means no attributes → getattr returns None
    return r


def _service(*results: RateLimitResult) -> RateLimiterService:
    """Build a service whose backend returns the given results in order."""
    backend = MagicMock()
    backend.check = AsyncMock(side_effect=list(results))
    key_builder = MagicMock()
    key_builder.build_key = AsyncMock(return_value="k")
    return RateLimiterService(
        backend=backend,
        key_builder=key_builder,
        failure_strategy=FailureStrategy.FAIL_OPEN,
    )


# ---------------------------------------------------------------------------
# AND group
# ---------------------------------------------------------------------------


async def test_and_group_blocks_on_first_blocked_policy() -> None:
    svc = _service(_make_result(False, "p1"), _make_result(True, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="AND")
    svc._provider._policies = [group]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    # Short-circuits after p1 blocks — p2 never evaluated
    assert len(results) == 1
    assert results[0].allowed is False
    assert svc._backend.check.call_count == 1  # noqa: SLF001


async def test_and_group_allows_when_all_pass() -> None:
    svc = _service(_make_result(True, "p1"), _make_result(True, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="AND")
    svc._provider._policies = [group]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    assert len(results) == 2
    assert all(r.allowed for r in results)


async def test_and_group_blocks_on_second_policy() -> None:
    svc = _service(_make_result(True, "p1"), _make_result(False, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="AND")
    svc._provider._policies = [group]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    assert len(results) == 2
    assert results[0].allowed is True
    assert results[1].allowed is False


# ---------------------------------------------------------------------------
# OR group
# ---------------------------------------------------------------------------


async def test_or_group_allows_when_any_passes() -> None:
    # p1 blocks, p2 allows → OR group allows
    svc = _service(_make_result(False, "p1"), _make_result(True, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="OR")
    svc._provider._policies = [group]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    # Both evaluated, OR allows because p2 passes
    assert len(results) == 2
    assert not all(r.allowed is False for r in results)


async def test_or_group_blocks_when_all_fail() -> None:
    svc = _service(_make_result(False, "p1"), _make_result(False, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="OR")
    svc._provider._policies = [group]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    assert len(results) == 2
    assert all(r.allowed is False for r in results)


async def test_or_group_evaluates_all_policies() -> None:
    """OR group never short-circuits — all policies are evaluated."""
    svc = _service(_make_result(True, "p1"), _make_result(False, "p2"))
    group = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="OR")
    svc._provider._policies = [group]  # noqa: SLF001
    await svc.check_request(_make_request())
    assert svc._backend.check.call_count == 2  # noqa: SLF001


# ---------------------------------------------------------------------------
# Nested groups
# ---------------------------------------------------------------------------


async def test_nested_and_inside_or() -> None:
    """OR(AND(p1, p2), p3): p1 allows, p2 blocks → inner AND blocks; p3 allows → OR allows."""
    svc = _service(
        _make_result(True, "p1"),  # inner AND p1 → allows
        _make_result(False, "p2"),  # inner AND p2 → blocks → AND blocks
        _make_result(True, "p3"),  # OR fallback p3 → allows → OR allows
    )
    inner_and = PolicyGroup(policies=[_make_policy("p1"), _make_policy("p2")], mode="AND")
    outer_or = PolicyGroup(policies=[inner_and, _make_policy("p3")], mode="OR")
    svc._provider._policies = [outer_or]  # noqa: SLF001
    results = await svc.check_request(_make_request())
    # OR allows because p3 passes
    assert any(r.allowed for r in results)


async def test_policy_group_default_mode_is_and() -> None:
    group = PolicyGroup(policies=[IPPolicy(limit="10/minute")])
    assert group.mode == "AND"


async def test_policy_group_name_defaults_empty() -> None:
    group = PolicyGroup(policies=[])
    assert group.name == ""
