"""Integration tests for RedisRateLimitBackend.

Note: fakeredis does not support Lua scripting (EVALSHA), which limits.storage.RedisStorage
uses for atomic operations. These tests use mocked limiter strategies to test the backend's
wrapping logic, error handling, and key management independently of the Lua limitation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from axiom.fastapi.rate_limiter.backend.redis import RedisRateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.exception import RateLimitBackendError


def _make_policy(
    limit: str = "3/minute",
    algorithm: Algorithm = Algorithm.FIXED_WINDOW,
) -> RateLimitPolicy:
    return RateLimitPolicy(limit=limit, scope=RateLimitScope.IP, algorithm=algorithm, name="test")


def _make_window_stats(reset_time: int = 9999999999, remaining: int = 5) -> MagicMock:
    stats = MagicMock()
    stats.reset_time = reset_time
    stats.remaining = remaining
    return stats


async def _async_iter(items: list) -> object:
    for item in items:
        yield item


@pytest.fixture
def fake_async_client() -> MagicMock:
    client = MagicMock()
    client.exists = AsyncMock(return_value=False)
    client.close = AsyncMock()
    client.delete = AsyncMock()
    client.scan_iter = MagicMock(return_value=_async_iter([]))
    return client


@pytest.fixture
def redis_backend(fake_async_client: MagicMock) -> RedisRateLimitBackend:
    with (
        patch("axiom.fastapi.rate_limiter.backend.redis.RedisStorage"),
        patch("axiom.fastapi.rate_limiter.backend.redis.FixedWindowRateLimiter"),
        patch("axiom.fastapi.rate_limiter.backend.redis.FixedWindowElasticExpiryRateLimiter"),
        patch("axiom.fastapi.rate_limiter.backend.redis.MovingWindowRateLimiter"),
    ):
        backend = RedisRateLimitBackend("redis://localhost:6379", fake_async_client)
    return backend


async def test_check_returns_allowed_result(redis_backend: RedisRateLimitBackend) -> None:
    stats = _make_window_stats(remaining=4)
    redis_backend._fixed.hit = MagicMock(return_value=True)  # noqa: SLF001
    redis_backend._fixed.get_window_stats = MagicMock(return_value=stats)  # noqa: SLF001

    result = await redis_backend.check("rl:ip:1.2.3.4", _make_policy())
    assert result.allowed is True
    assert result.remaining == 4


async def test_check_returns_blocked_result_when_hit_returns_false(
    redis_backend: RedisRateLimitBackend,
) -> None:
    stats = _make_window_stats(remaining=0)
    redis_backend._fixed.hit = MagicMock(return_value=False)  # noqa: SLF001
    redis_backend._fixed.get_window_stats = MagicMock(return_value=stats)  # noqa: SLF001

    result = await redis_backend.check("rl:ip:1.2.3.4", _make_policy())
    assert result.allowed is False
    assert result.remaining == 0


async def test_check_wraps_exceptions_in_backend_error(
    redis_backend: RedisRateLimitBackend,
) -> None:
    redis_backend._fixed.hit = MagicMock(side_effect=Exception("connection refused"))  # noqa: SLF001

    with pytest.raises(RateLimitBackendError):
        await redis_backend.check("rl:ip:1.2.3.4", _make_policy())


async def test_reset_scans_and_deletes_matching_keys(
    redis_backend: RedisRateLimitBackend,
    fake_async_client: MagicMock,
) -> None:
    matched_key = "LIMITS:LIMITER/rl:ip:1.2.3.4/3/1/minute"
    fake_async_client.scan_iter = MagicMock(return_value=_async_iter([matched_key]))

    await redis_backend.reset("rl:ip:1.2.3.4")

    fake_async_client.scan_iter.assert_called_once_with("*/rl:ip:1.2.3.4/*")  # noqa: SLF001
    fake_async_client.delete.assert_called_once_with(matched_key)  # noqa: SLF001


async def test_reset_wraps_exceptions_in_backend_error(
    redis_backend: RedisRateLimitBackend,
    fake_async_client: MagicMock,
) -> None:
    async def _raise() -> object:
        raise RuntimeError("scan error")
        yield  # make it an async generator

    fake_async_client.scan_iter = MagicMock(return_value=_raise())
    with pytest.raises(RateLimitBackendError):
        await redis_backend.reset("rl:ip:1.2.3.4")


async def test_startup_validates_connectivity(
    redis_backend: RedisRateLimitBackend,
    fake_async_client: MagicMock,
) -> None:
    await redis_backend.startup()
    fake_async_client.exists.assert_called_once_with("ping_probe")


async def test_startup_raises_backend_error_on_failure(
    redis_backend: RedisRateLimitBackend,
    fake_async_client: MagicMock,
) -> None:
    fake_async_client.exists = AsyncMock(side_effect=Exception("timeout"))
    with pytest.raises(RateLimitBackendError):
        await redis_backend.startup()


async def test_shutdown_closes_client(
    redis_backend: RedisRateLimitBackend,
    fake_async_client: MagicMock,
) -> None:
    await redis_backend.shutdown()
    fake_async_client.close.assert_called_once()


async def test_sliding_window_uses_elastic_limiter(redis_backend: RedisRateLimitBackend) -> None:
    stats = _make_window_stats(remaining=2)
    redis_backend._elastic.hit = MagicMock(return_value=True)  # noqa: SLF001
    redis_backend._elastic.get_window_stats = MagicMock(return_value=stats)  # noqa: SLF001

    policy = _make_policy(algorithm=Algorithm.SLIDING_WINDOW)
    result = await redis_backend.check("key", policy)
    assert result.allowed is True
    redis_backend._elastic.hit.assert_called_once()  # noqa: SLF001


async def test_moving_window_uses_moving_limiter(redis_backend: RedisRateLimitBackend) -> None:
    stats = _make_window_stats(remaining=1)
    redis_backend._moving.hit = MagicMock(return_value=True)  # noqa: SLF001
    redis_backend._moving.get_window_stats = MagicMock(return_value=stats)  # noqa: SLF001

    policy = _make_policy(algorithm=Algorithm.MOVING_WINDOW)
    result = await redis_backend.check("key", policy)
    assert result.allowed is True
    redis_backend._moving.hit.assert_called_once()  # noqa: SLF001
