"""Test configuration for axiom-cache."""

import fakeredis
import fakeredis.aioredis
import pytest

from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache
from axiom.cache.redis import AsyncRedisCache, SyncRedisCache
from axiom.redis.async_client import AsyncRedisClient
from axiom.redis.sync_client import SyncRedisClient


@pytest.fixture
def async_inmemory() -> AsyncInMemoryCache:
    """Return a fresh AsyncInMemoryCache."""
    return AsyncInMemoryCache()


@pytest.fixture
def sync_inmemory() -> SyncInMemoryCache:
    """Return a fresh SyncInMemoryCache."""
    return SyncInMemoryCache()


@pytest.fixture
def fake_sync_redis() -> fakeredis.FakeRedis:
    """Return a FakeRedis sync client."""
    return fakeredis.FakeRedis()


@pytest.fixture
async def fake_async_redis() -> fakeredis.aioredis.FakeRedis:
    """Return a FakeRedis async client."""
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def sync_redis_cache(fake_sync_redis: fakeredis.FakeRedis) -> SyncRedisCache:
    """Return a SyncRedisCache backed by fakeredis."""
    client = SyncRedisClient(fake_sync_redis)
    return SyncRedisCache(client)


@pytest.fixture
async def async_redis_cache(fake_async_redis: fakeredis.aioredis.FakeRedis) -> AsyncRedisCache:
    """Return an AsyncRedisCache backed by fakeredis."""
    client = AsyncRedisClient(fake_async_redis)
    return AsyncRedisCache(client)
