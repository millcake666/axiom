"""Tests for the @invalidate decorator."""

from axiom.cache.decorators.cached import cached
from axiom.cache.decorators.invalidate import invalidate
from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache
from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker
from axiom.cache.schemas import CacheInvalidateParams, ConvertParam


class TestInvalidateDecoratorAsync:
    """Tests for @invalidate with async functions."""

    async def test_invalidates_cached_entry(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Invalidation clears cached entries for the target function."""
        km = FunctionKeyMaker()
        call_count = 0

        @cached(async_inmemory, key_maker=km)
        async def get_item(item_id: int) -> str:
            nonlocal call_count
            call_count += 1
            return f"item_{item_id}"

        # Populate cache
        await get_item(1)
        assert call_count == 1
        await get_item(1)
        assert call_count == 1  # from cache

        @invalidate(
            CacheInvalidateParams(functions=[get_item]),
            backend=async_inmemory,
            key_maker=km,
        )
        async def update_item(item_id: int) -> None:
            pass

        await update_item(1)
        # Cache should be cleared
        await get_item(1)
        assert call_count == 2

    async def test_does_not_invalidate_unrelated(
        self,
        async_inmemory: AsyncInMemoryCache,
    ) -> None:
        """Invalidation with params only removes matching entries."""
        km = FunctionKeyMaker()

        @cached(async_inmemory, key_maker=km)
        async def get_user(user_id: int) -> str:
            return f"user_{user_id}"

        await get_user(1)
        await get_user(2)

        @invalidate(
            CacheInvalidateParams(
                functions=[get_user],
                params=[ConvertParam(wrapped_func_param="user_id")],
            ),
            backend=async_inmemory,
            key_maker=km,
        )
        async def update_user(user_id: int) -> None:
            pass

        await update_user(1)
        # user_id=1 cache cleared, user_id=2 should remain
        # (inmemory delete_by_pattern with param "user_id=1" filters correctly)
        entry_2 = await async_inmemory.get(km.make_key(get_user, 2))
        assert entry_2 == "user_2"


class TestInvalidateDecoratorSync:
    """Tests for @invalidate with sync functions."""

    def test_invalidates_cached_entry(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Sync invalidation clears cached entries for the target function."""
        km = FunctionKeyMaker()
        call_count = 0

        @cached(sync_inmemory, key_maker=km)
        def get_item(item_id: int) -> str:
            nonlocal call_count
            call_count += 1
            return f"item_{item_id}"

        get_item(10)
        assert call_count == 1
        get_item(10)
        assert call_count == 1

        @invalidate(
            CacheInvalidateParams(functions=[get_item]),
            backend=sync_inmemory,
            key_maker=km,
        )
        def update_item(item_id: int) -> None:
            pass

        update_item(10)
        get_item(10)
        assert call_count == 2

    def test_preserves_function_name(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Decorator preserves __name__ of wrapped function."""

        @invalidate(
            CacheInvalidateParams(functions=[lambda: None]),
            backend=sync_inmemory,
        )
        def my_invalidator() -> None:
            pass

        assert my_invalidator.__name__ == "my_invalidator"
