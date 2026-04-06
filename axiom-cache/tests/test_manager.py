"""Tests for CacheManager."""

from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache
from axiom.cache.manager import CacheManager
from axiom.cache.schemas import CacheInvalidateParams


class TestCacheManagerAsync:
    """Tests for CacheManager with async backend."""

    async def test_cached_decorator(self, async_inmemory: AsyncInMemoryCache) -> None:
        """CacheManager.cached() produces a working decorator."""
        manager = CacheManager(async_inmemory, default_ttl=0)
        call_count = 0

        @manager.cached()
        async def get_value(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert await get_value(5) == 10
        assert await get_value(5) == 10
        assert call_count == 1

    async def test_cached_with_custom_ttl(self, async_inmemory: AsyncInMemoryCache) -> None:
        """CacheManager.cached(ttl=...) overrides default_ttl."""
        manager = CacheManager(async_inmemory, default_ttl=0)

        @manager.cached(ttl=60)
        async def fn(x: int) -> str:
            return f"v{x}"

        assert await fn(1) == "v1"
        assert await fn(1) == "v1"

    async def test_invalidate_decorator(self, async_inmemory: AsyncInMemoryCache) -> None:
        """CacheManager.invalidate() produces a working invalidation decorator."""
        manager = CacheManager(async_inmemory)
        call_count = 0

        @manager.cached()
        async def get_val(key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"val_{key}"

        await get_val("a")
        assert call_count == 1

        @manager.invalidate(CacheInvalidateParams(functions=[get_val]))
        async def clear_val(key: str) -> None:
            pass

        await clear_val("a")
        await get_val("a")
        assert call_count == 2


class TestCacheManagerSync:
    """Tests for CacheManager with sync backend."""

    def test_cached_decorator(self, sync_inmemory: SyncInMemoryCache) -> None:
        """CacheManager.cached() produces a working sync decorator."""
        manager = CacheManager(sync_inmemory)
        call_count = 0

        @manager.cached()
        def get_value(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x + 1

        assert get_value(3) == 4
        assert get_value(3) == 4
        assert call_count == 1

    def test_default_ttl_used(self, sync_inmemory: SyncInMemoryCache) -> None:
        """default_ttl is passed to cached decorator."""
        manager = CacheManager(sync_inmemory, default_ttl=3600)

        @manager.cached()
        def fn() -> str:
            return "result"

        assert fn() == "result"
