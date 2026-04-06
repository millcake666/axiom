"""Tests for AsyncRedisCache and SyncRedisCache using fakeredis."""

from axiom.cache.redis import AsyncRedisCache, SyncRedisCache


class TestAsyncRedisCache:
    """Tests for AsyncRedisCache."""

    async def test_set_and_get(self, async_redis_cache: AsyncRedisCache) -> None:
        """Set a value and retrieve it."""
        await async_redis_cache.set("key", {"hello": "world"})
        result = await async_redis_cache.get("key")
        assert result == {"hello": "world"}

    async def test_get_missing(self, async_redis_cache: AsyncRedisCache) -> None:
        """Get returns None for missing key."""
        result = await async_redis_cache.get("missing")
        assert result is None

    async def test_set_with_ttl(self, async_redis_cache: AsyncRedisCache) -> None:
        """Set with TTL stores the value."""
        await async_redis_cache.set("ttl_key", [1, 2, 3], ttl=60)
        result = await async_redis_cache.get("ttl_key")
        assert result == [1, 2, 3]

    async def test_delete(self, async_redis_cache: AsyncRedisCache) -> None:
        """Delete removes a key."""
        await async_redis_cache.set("k", "v")
        await async_redis_cache.delete("k")
        assert await async_redis_cache.get("k") is None

    async def test_exists_true(self, async_redis_cache: AsyncRedisCache) -> None:
        """Exists returns True for existing key."""
        await async_redis_cache.set("k", "v")
        assert await async_redis_cache.exists("k") is True

    async def test_exists_false(self, async_redis_cache: AsyncRedisCache) -> None:
        """Exists returns False for missing key."""
        assert await async_redis_cache.exists("absent") is False

    async def test_delete_all(self, async_redis_cache: AsyncRedisCache) -> None:
        """delete_all flushes all keys."""
        await async_redis_cache.set("a", 1)
        await async_redis_cache.set("b", 2)
        await async_redis_cache.delete_all()
        assert await async_redis_cache.get("a") is None

    async def test_delete_by_pattern(self, async_redis_cache: AsyncRedisCache) -> None:
        """delete_by_pattern removes matching keys."""
        await async_redis_cache.set("ns:a", 1)
        await async_redis_cache.set("ns:b", 2)
        await async_redis_cache.set("other", 3)
        await async_redis_cache.delete_by_pattern("ns:*")
        assert await async_redis_cache.get("ns:a") is None
        assert await async_redis_cache.get("ns:b") is None
        assert await async_redis_cache.get("other") == 3

    async def test_delete_by_pattern_with_params(self, async_redis_cache: AsyncRedisCache) -> None:
        """delete_by_pattern with params filters correctly."""
        await async_redis_cache.set("fn:id=1:m", 1)
        await async_redis_cache.set("fn:id=2:m", 2)
        await async_redis_cache.delete_by_pattern("fn:*", ["id=1"])
        assert await async_redis_cache.get("fn:id=1:m") is None
        assert await async_redis_cache.get("fn:id=2:m") == 2


class TestSyncRedisCache:
    """Tests for SyncRedisCache."""

    def test_set_and_get(self, sync_redis_cache: SyncRedisCache) -> None:
        """Set a value and retrieve it."""
        sync_redis_cache.set("key", {"hello": "world"})
        result = sync_redis_cache.get("key")
        assert result == {"hello": "world"}

    def test_get_missing(self, sync_redis_cache: SyncRedisCache) -> None:
        """Get returns None for missing key."""
        result = sync_redis_cache.get("missing")
        assert result is None

    def test_set_with_ttl(self, sync_redis_cache: SyncRedisCache) -> None:
        """Set with TTL stores the value."""
        sync_redis_cache.set("ttl_key", [1, 2], ttl=60)
        result = sync_redis_cache.get("ttl_key")
        assert result == [1, 2]

    def test_delete(self, sync_redis_cache: SyncRedisCache) -> None:
        """Delete removes a key."""
        sync_redis_cache.set("k", "v")
        sync_redis_cache.delete("k")
        assert sync_redis_cache.get("k") is None

    def test_exists_true(self, sync_redis_cache: SyncRedisCache) -> None:
        """Exists returns True for existing key."""
        sync_redis_cache.set("k", "v")
        assert sync_redis_cache.exists("k") is True

    def test_exists_false(self, sync_redis_cache: SyncRedisCache) -> None:
        """Exists returns False for missing key."""
        assert sync_redis_cache.exists("absent") is False

    def test_delete_all(self, sync_redis_cache: SyncRedisCache) -> None:
        """delete_all flushes all keys."""
        sync_redis_cache.set("a", 1)
        sync_redis_cache.delete_all()
        assert sync_redis_cache.get("a") is None

    def test_delete_by_pattern(self, sync_redis_cache: SyncRedisCache) -> None:
        """delete_by_pattern removes matching keys."""
        sync_redis_cache.set("ns:a", 1)
        sync_redis_cache.set("ns:b", 2)
        sync_redis_cache.set("other", 3)
        sync_redis_cache.delete_by_pattern("ns:*")
        assert sync_redis_cache.get("ns:a") is None
        assert sync_redis_cache.get("ns:b") is None
        assert sync_redis_cache.get("other") == 3
