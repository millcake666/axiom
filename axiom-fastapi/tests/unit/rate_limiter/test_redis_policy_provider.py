"""Unit tests for RedisPolicyProvider (serialization, versioning, error handling)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import IPPolicy, PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.policy_provider.exception import PolicyProviderError
from axiom.fastapi.rate_limiter.policy_provider.redis import (
    RedisPolicyProvider,
    _deserialize_item,
    _serialize_item,
)


def _ctx() -> RequestContext:
    return RequestContext(path="/", method="GET", client_ip="127.0.0.1")


def _policy(name: str = "p") -> RateLimitPolicy:
    return RateLimitPolicy(limit="10/minute", scope=RateLimitScope.IP, name=name)


def _redis_client(*, get_value: object = None) -> MagicMock:
    client = MagicMock()
    client.get = AsyncMock(return_value=get_value)
    client.set = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# get_policies
# ---------------------------------------------------------------------------


async def test_get_policies_returns_empty_list_when_key_absent() -> None:
    provider = RedisPolicyProvider(_redis_client(get_value=None), env="test")
    result = await provider.get_policies(_ctx())
    assert result == []


async def test_get_policies_deserializes_stored_policies() -> None:
    policies = [_policy("a"), _policy("b")]
    payload = json.dumps({"version": 1, "policies": [_serialize_item(p) for p in policies]})
    provider = RedisPolicyProvider(_redis_client(get_value=payload.encode()), env="test")
    result = await provider.get_policies(_ctx())
    assert len(result) == 2
    assert result[0].name == "a"
    assert result[1].name == "b"


async def test_get_policies_raises_on_redis_error() -> None:
    client = MagicMock()
    client.get = AsyncMock(side_effect=RuntimeError("connection refused"))
    provider = RedisPolicyProvider(client, env="test")
    with pytest.raises(PolicyProviderError, match="Failed to read policies"):
        await provider.get_policies(_ctx())


async def test_get_policies_raises_on_malformed_json() -> None:
    provider = RedisPolicyProvider(_redis_client(get_value=b"not-json"), env="test")
    with pytest.raises(PolicyProviderError, match="Malformed policy payload"):
        await provider.get_policies(_ctx())


# ---------------------------------------------------------------------------
# set_policies / versioning
# ---------------------------------------------------------------------------


async def test_set_policies_increments_version() -> None:
    existing = json.dumps({"version": 5, "policies": []}).encode()
    client = _redis_client(get_value=existing)
    provider = RedisPolicyProvider(client, env="test")
    await provider.set_policies([_policy()])
    call_args = client.set.call_args
    saved = json.loads(call_args[0][1])
    assert saved["version"] == 6


async def test_set_policies_starts_at_version_1_when_no_existing() -> None:
    client = _redis_client(get_value=None)
    provider = RedisPolicyProvider(client, env="test")
    await provider.set_policies([_policy()])
    saved = json.loads(client.set.call_args[0][1])
    assert saved["version"] == 1


async def test_get_version_returns_none_when_absent() -> None:
    provider = RedisPolicyProvider(_redis_client(get_value=None), env="test")
    assert await provider.get_version() is None


async def test_get_version_returns_correct_value() -> None:
    payload = json.dumps({"version": 42, "policies": []}).encode()
    provider = RedisPolicyProvider(_redis_client(get_value=payload), env="test")
    assert await provider.get_version() == 42


# ---------------------------------------------------------------------------
# Env namespacing
# ---------------------------------------------------------------------------


async def test_key_includes_env_label() -> None:
    client = _redis_client(get_value=None)
    provider = RedisPolicyProvider(client, env="staging")
    await provider.get_policies(_ctx())
    client.get.assert_called_once_with("rl:staging:policies")


# ---------------------------------------------------------------------------
# Serialization roundtrip
# ---------------------------------------------------------------------------


def test_policy_serialization_roundtrip() -> None:
    original = _policy("roundtrip")
    data = _serialize_item(original)
    restored = _deserialize_item(data)
    assert isinstance(restored, RateLimitPolicy)
    assert restored.limit == original.limit
    assert restored.scope == original.scope
    assert restored.name == original.name


def test_policy_group_serialization_roundtrip() -> None:
    group = PolicyGroup(
        policies=[_policy("a"), _policy("b")],
        mode="OR",
        name="my_group",
    )
    data = _serialize_item(group)
    restored = _deserialize_item(data)
    assert isinstance(restored, PolicyGroup)
    assert restored.mode == "OR"
    assert restored.name == "my_group"
    assert len(restored.policies) == 2


def test_ip_policy_class_preserved_in_roundtrip() -> None:
    original = IPPolicy(limit="5/second", name="ip_p")
    data = _serialize_item(original)
    restored = _deserialize_item(data)
    assert isinstance(restored, IPPolicy)
