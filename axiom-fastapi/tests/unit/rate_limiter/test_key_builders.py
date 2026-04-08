"""Unit tests for axiom.fastapi.rate_limiter.key_builder implementations."""

from unittest.mock import MagicMock

import pytest

from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.exception import RateLimitError
from axiom.fastapi.rate_limiter.key_builder.api_key import ApiKeyKeyBuilder
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from axiom.fastapi.rate_limiter.key_builder.user_id import UserIdKeyBuilder


def _make_policy() -> RateLimitPolicy:
    return RateLimitPolicy(limit="10/minute", scope=RateLimitScope.IP, key_prefix="rl")


def _mock_request(
    headers: dict[str, str] | None = None,
    client_host: str = "127.0.0.1",
) -> MagicMock:
    request = MagicMock()
    request.headers = headers or {}
    request.client = MagicMock()
    request.client.host = client_host
    request.state = MagicMock(spec=[])
    return request


async def test_ip_builder_uses_forwarded_for() -> None:
    request = _mock_request(headers={"X-Forwarded-For": "10.0.0.1, 192.168.1.1"})
    builder = IPKeyBuilder()
    key = await builder.build_key(request, _make_policy())
    assert key == "rl:ip:10.0.0.1"


async def test_ip_builder_falls_back_to_client_host() -> None:
    request = _mock_request(headers={}, client_host="192.168.5.5")
    builder = IPKeyBuilder()
    key = await builder.build_key(request, _make_policy())
    assert key == "rl:ip:192.168.5.5"


async def test_api_key_builder_hashes_header() -> None:
    request = _mock_request(headers={"X-API-Key": "my-secret-key"})
    builder = ApiKeyKeyBuilder()
    key = await builder.build_key(request, _make_policy())
    import hashlib

    expected_hash = hashlib.sha256(b"my-secret-key").hexdigest()[:16]
    assert key == f"rl:apikey:{expected_hash}"


async def test_api_key_builder_custom_header() -> None:
    request = _mock_request(headers={"Authorization": "Bearer token123"})
    builder = ApiKeyKeyBuilder(header_name="Authorization")
    key = await builder.build_key(request, _make_policy())
    assert key.startswith("rl:apikey:")


async def test_user_id_builder_reads_from_state() -> None:
    request = _mock_request()
    request.state.user_id = "user-42"
    builder = UserIdKeyBuilder()
    key = await builder.build_key(request, _make_policy())
    assert key == "rl:user:user-42"


async def test_user_id_builder_raises_when_user_id_absent() -> None:
    request = _mock_request()
    # state has spec=[] so no attributes
    builder = UserIdKeyBuilder()
    with pytest.raises(RateLimitError):
        await builder.build_key(request, _make_policy())


async def test_user_id_builder_custom_state_attr() -> None:
    request = _mock_request()
    request.state = MagicMock()
    request.state.sub = "user-99"
    builder = UserIdKeyBuilder(state_attr="sub")
    key = await builder.build_key(request, _make_policy())
    assert key == "rl:user:user-99"
