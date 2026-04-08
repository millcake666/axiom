"""Integration tests for InMemoryRateLimitBackend using real limits engine."""

import asyncio

from axiom.fastapi.rate_limiter.backend.memory import InMemoryRateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.policy import RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope


def _make_policy(
    limit: str = "3/minute",
    algorithm: Algorithm = Algorithm.FIXED_WINDOW,
) -> RateLimitPolicy:
    return RateLimitPolicy(limit=limit, scope=RateLimitScope.IP, algorithm=algorithm, name="test")


async def test_fixed_window_blocks_on_n_plus_1_request() -> None:
    backend = InMemoryRateLimitBackend()
    policy = _make_policy("3/minute")
    key = "test:ip:1.2.3.4"

    for _ in range(3):
        result = await backend.check(key, policy)
        assert result.allowed is True

    result = await backend.check(key, policy)
    assert result.allowed is False


async def test_remaining_decrements_correctly() -> None:
    backend = InMemoryRateLimitBackend()
    policy = _make_policy("5/minute")
    key = "test:ip:remaining"

    result = await backend.check(key, policy)
    assert result.remaining == 4

    result = await backend.check(key, policy)
    assert result.remaining == 3


async def test_reset_clears_counter() -> None:
    backend = InMemoryRateLimitBackend()
    policy = _make_policy("2/minute")
    key = "test:ip:reset"

    await backend.check(key, policy)
    await backend.check(key, policy)
    blocked = await backend.check(key, policy)
    assert blocked.allowed is False

    await backend.reset(key)

    result = await backend.check(key, policy)
    assert result.allowed is True


async def test_sliding_window_allows_after_window_expires() -> None:
    backend = InMemoryRateLimitBackend()
    # Use a very short window — 2 requests per 1 second
    policy = _make_policy("2/1second", Algorithm.SLIDING_WINDOW)
    key = "test:ip:sliding"

    r1 = await backend.check(key, policy)
    r2 = await backend.check(key, policy)
    assert r1.allowed is True
    assert r2.allowed is True

    blocked = await backend.check(key, policy)
    assert blocked.allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.1)

    result = await backend.check(key, policy)
    assert result.allowed is True


async def test_get_remaining_does_not_increment() -> None:
    backend = InMemoryRateLimitBackend()
    policy = _make_policy("10/minute")
    key = "test:ip:get_remaining"

    await backend.check(key, policy)
    remaining = await backend.get_remaining(key, policy)
    # Should still be 9 — get_remaining doesn't consume a slot
    assert remaining == 9
