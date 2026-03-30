"""Test configuration for axiom-redis."""

import fakeredis
import fakeredis.aioredis
import pytest

from axiom.redis.async_client import AsyncRedisClient
from axiom.redis.sync_client import SyncRedisClient


@pytest.fixture
def fake_redis() -> fakeredis.FakeRedis:
    """Return a FakeRedis sync client."""
    return fakeredis.FakeRedis()


@pytest.fixture
async def fake_async_redis() -> fakeredis.aioredis.FakeRedis:
    """Return a FakeRedis async client."""
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def sync_client(fake_redis: fakeredis.FakeRedis) -> SyncRedisClient:
    """Return a SyncRedisClient backed by fakeredis."""
    return SyncRedisClient(fake_redis)


@pytest.fixture
async def async_client(fake_async_redis: fakeredis.aioredis.FakeRedis) -> AsyncRedisClient:
    """Return an AsyncRedisClient backed by fakeredis."""
    return AsyncRedisClient(fake_async_redis)
