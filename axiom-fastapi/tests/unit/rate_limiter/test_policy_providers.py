"""Unit tests for StaticPolicyProvider, InMemoryPolicyProvider, CachedPolicyProvider."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import IPPolicy, PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.policy_provider.cached import CachedPolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.memory import InMemoryPolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.static import StaticPolicyProvider


def _ctx() -> RequestContext:
    return RequestContext(path="/test", method="GET", client_ip="127.0.0.1")


def _policy(name: str = "p") -> RateLimitPolicy:
    return RateLimitPolicy(limit="10/minute", scope=RateLimitScope.IP, name=name)


# ---------------------------------------------------------------------------
# StaticPolicyProvider
# ---------------------------------------------------------------------------


async def test_static_provider_returns_same_list_every_call() -> None:
    policies = [_policy("a"), _policy("b")]
    provider = StaticPolicyProvider(policies)
    ctx = _ctx()
    result1 = await provider.get_policies(ctx)
    result2 = await provider.get_policies(ctx)
    assert result1 == policies
    assert result2 == policies


async def test_static_provider_returns_empty_list_when_initialized_empty() -> None:
    provider = StaticPolicyProvider([])
    result = await provider.get_policies(_ctx())
    assert result == []


async def test_static_provider_accepts_policy_groups() -> None:
    group = PolicyGroup(policies=[IPPolicy(limit="5/second")], mode="OR")
    provider = StaticPolicyProvider([group])
    result = await provider.get_policies(_ctx())
    assert len(result) == 1
    assert isinstance(result[0], PolicyGroup)


# ---------------------------------------------------------------------------
# InMemoryPolicyProvider
# ---------------------------------------------------------------------------


async def test_inmemory_provider_returns_initial_policies() -> None:
    policies = [_policy("x")]
    provider = InMemoryPolicyProvider(policies)
    result = await provider.get_policies(_ctx())
    assert result == policies


async def test_inmemory_provider_defaults_to_empty() -> None:
    provider = InMemoryPolicyProvider()
    result = await provider.get_policies(_ctx())
    assert result == []


async def test_inmemory_provider_set_policies_replaces_list() -> None:
    provider = InMemoryPolicyProvider([_policy("old")])
    new_policies = [_policy("new1"), _policy("new2")]
    await provider.set_policies(new_policies)
    result = await provider.get_policies(_ctx())
    assert result == new_policies


async def test_inmemory_provider_returns_copy_not_reference() -> None:
    policies = [_policy("a")]
    provider = InMemoryPolicyProvider(policies)
    result = await provider.get_policies(_ctx())
    result.append(_policy("b"))  # mutate returned list
    # Provider's internal list should not be affected
    assert len(await provider.get_policies(_ctx())) == 1


# ---------------------------------------------------------------------------
# CachedPolicyProvider
# ---------------------------------------------------------------------------


async def test_cached_provider_calls_inner_once_within_ttl() -> None:
    inner = MagicMock()
    inner.get_policies = AsyncMock(return_value=[_policy("p")])
    provider = CachedPolicyProvider(inner, ttl=60.0)
    ctx = _ctx()

    await provider.get_policies(ctx)
    await provider.get_policies(ctx)
    await provider.get_policies(ctx)

    assert inner.get_policies.call_count == 1


async def test_cached_provider_refreshes_after_ttl_expires() -> None:
    inner = MagicMock()
    inner.get_policies = AsyncMock(return_value=[_policy("p")])
    provider = CachedPolicyProvider(inner, ttl=0.05)  # 50ms TTL
    ctx = _ctx()

    await provider.get_policies(ctx)
    await asyncio.sleep(0.1)  # exceed TTL
    await provider.get_policies(ctx)

    assert inner.get_policies.call_count == 2


async def test_cached_provider_invalidate_forces_refresh() -> None:
    inner = MagicMock()
    inner.get_policies = AsyncMock(return_value=[_policy("p")])
    provider = CachedPolicyProvider(inner, ttl=60.0)
    ctx = _ctx()

    await provider.get_policies(ctx)
    provider.invalidate()
    await provider.get_policies(ctx)

    assert inner.get_policies.call_count == 2


async def test_cached_provider_serves_stale_cache_on_inner_error() -> None:
    """When inner provider fails after cache expires, stale cache is returned (fail-open)."""
    inner = MagicMock()
    stale = [_policy("stale")]
    inner.get_policies = AsyncMock(side_effect=[stale, RuntimeError("boom")])
    provider = CachedPolicyProvider(inner, ttl=0.05)
    ctx = _ctx()

    result1 = await provider.get_policies(ctx)  # warm up cache
    await asyncio.sleep(0.1)  # let TTL expire (cache ages but is not cleared)
    result2 = await provider.get_policies(ctx)  # inner fails → serve stale

    assert result1 == stale
    assert result2 == stale  # stale cache returned, not exception


async def test_cached_provider_propagates_error_on_cold_cache() -> None:
    """When cache is cold and inner provider fails, the error propagates."""
    inner = MagicMock()
    inner.get_policies = AsyncMock(side_effect=RuntimeError("cold miss"))
    provider = CachedPolicyProvider(inner, ttl=60.0)

    with pytest.raises(RuntimeError, match="cold miss"):
        await provider.get_policies(_ctx())
