"""Tests for the @cached decorator."""

from axiom.cache.decorators.cached import cached
from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache


class TestCachedDecoratorAsync:
    """Tests for @cached with async functions."""

    async def test_caches_result(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Function result is cached on first call."""
        call_count = 0

        @cached(async_inmemory)
        async def expensive(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await expensive(5)
        result2 = await expensive(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    async def test_different_args_not_shared(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Different arguments produce separate cache entries."""

        @cached(async_inmemory)
        async def fn(x: int) -> int:
            return x + 1

        assert await fn(1) == 2
        assert await fn(2) == 3

    async def test_with_ttl(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Cache with TTL still works on first call."""

        @cached(async_inmemory, ttl=60)
        async def fn(x: int) -> str:
            return f"val_{x}"

        result = await fn(42)
        assert result == "val_42"
        # Cached on second call
        result2 = await fn(42)
        assert result2 == "val_42"


class TestCachedDecoratorSync:
    """Tests for @cached with sync functions."""

    def test_caches_result(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Function result is cached on first call."""
        call_count = 0

        @cached(sync_inmemory)
        def expensive(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 3

        result1 = expensive(5)
        result2 = expensive(5)
        assert result1 == 15
        assert result2 == 15
        assert call_count == 1

    def test_different_args_not_shared(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Different arguments produce separate cache entries."""

        @cached(sync_inmemory)
        def fn(x: int) -> int:
            return x + 10

        assert fn(1) == 11
        assert fn(2) == 12

    def test_preserves_function_name(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Decorator preserves __name__ of wrapped function."""

        @cached(sync_inmemory)
        def my_func() -> None:
            pass

        assert my_func.__name__ == "my_func"
