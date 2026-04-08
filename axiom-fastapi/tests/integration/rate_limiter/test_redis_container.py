"""Integration tests for RedisRateLimitBackend with a real Redis via testcontainers.

Run with: pytest -m slow
"""

import os
import socket as _socket

import pytest

from axiom.fastapi.rate_limiter.backend.redis import RedisRateLimitBackend
from axiom.fastapi.rate_limiter.core.policy import IPPolicy

_DOCKER_SOCKET_CANDIDATES = [
    os.environ.get("DOCKER_HOST", "").removeprefix("unix://"),
    "/var/run/docker.sock",
    os.path.expanduser("~/.docker/run/docker.sock"),
]


def _resolve_docker_host() -> bool:
    """Set DOCKER_HOST and TESTCONTAINERS_RYUK_DISABLED for macOS Docker Desktop.

    Returns True if a usable Docker socket was found.
    Ryuk is disabled because it tries to mount the Docker socket into a container,
    which fails with non-standard socket paths on macOS Docker Desktop.
    """
    if os.environ.get("DOCKER_HOST"):
        return True

    for path in _DOCKER_SOCKET_CANDIDATES:
        if not path:
            continue
        try:
            s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(path)
            s.close()
            os.environ["DOCKER_HOST"] = f"unix://{path}"
            os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
            return True
        except OSError:
            continue
    return False


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not _resolve_docker_host(), reason="Docker not available"),
]


@pytest.fixture(scope="module")
def redis_url() -> str:
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)
        yield f"redis://{host}:{port}"


@pytest.fixture
async def redis_backend(redis_url: str) -> RedisRateLimitBackend:
    import redis.asyncio as aioredis

    from axiom.redis.async_client import AsyncRedisClient

    raw = aioredis.Redis.from_url(redis_url, decode_responses=True)
    client = AsyncRedisClient(raw)
    backend = RedisRateLimitBackend(redis_url=redis_url, async_redis_client=client)
    await backend.startup()
    # Flush before each test for isolation
    await raw.flushall()
    yield backend
    await backend.shutdown()


async def test_redis_allows_requests_under_limit(redis_backend: RedisRateLimitBackend) -> None:
    policy = IPPolicy(limit="3/minute", name="test")
    for _ in range(3):
        result = await redis_backend.check("test:ip:1", policy)
        assert result.allowed is True


async def test_redis_blocks_after_limit_exceeded(redis_backend: RedisRateLimitBackend) -> None:
    policy = IPPolicy(limit="2/minute", name="test")
    await redis_backend.check("test:ip:2", policy)
    await redis_backend.check("test:ip:2", policy)
    result = await redis_backend.check("test:ip:2", policy)
    assert result.allowed is False
    assert result.remaining == 0


async def test_redis_remaining_decrements(redis_backend: RedisRateLimitBackend) -> None:
    policy = IPPolicy(limit="5/minute", name="test")
    r1 = await redis_backend.check("test:ip:3", policy)
    r2 = await redis_backend.check("test:ip:3", policy)
    assert r1.remaining > r2.remaining


async def test_redis_reset_clears_counter(redis_backend: RedisRateLimitBackend) -> None:
    policy = IPPolicy(limit="1/minute", name="test")
    await redis_backend.check("test:ip:4", policy)
    blocked = await redis_backend.check("test:ip:4", policy)
    assert blocked.allowed is False

    await redis_backend.reset("test:ip:4")
    result = await redis_backend.check("test:ip:4", policy)
    assert result.allowed is True


async def test_redis_different_keys_are_independent(redis_backend: RedisRateLimitBackend) -> None:
    policy = IPPolicy(limit="1/minute", name="test")
    await redis_backend.check("test:ip:A", policy)
    r = await redis_backend.check("test:ip:B", policy)
    assert r.allowed is True
