"""Tests for AsyncInMemoryCache and SyncInMemoryCache."""

from __future__ import annotations

import asyncio
import time

import pytest

from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache


class TestAsyncInMemoryCache:
    """Tests for AsyncInMemoryCache."""

    async def test_set_and_get(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Set a value and retrieve it."""
        await async_inmemory.set("key", "value")
        result = await async_inmemory.get("key")
        assert result == "value"

    async def test_get_missing(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Get returns None for missing key."""
        result = await async_inmemory.get("missing")
        assert result is None

    async def test_delete(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Delete removes a key."""
        await async_inmemory.set("k", "v")
        await async_inmemory.delete("k")
        assert await async_inmemory.get("k") is None

    async def test_delete_missing(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Delete on missing key does not raise."""
        await async_inmemory.delete("ghost")

    async def test_exists_true(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Exists returns True for existing key."""
        await async_inmemory.set("k", "v")
        assert await async_inmemory.exists("k") is True

    async def test_exists_false(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Exists returns False for missing key."""
        assert await async_inmemory.exists("absent") is False

    async def test_ttl_expiry(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Value expires after TTL."""
        await async_inmemory.set("exp", "value", ttl=1)
        assert await async_inmemory.get("exp") == "value"
        # Simulate expiry by manipulating time indirectly via small TTL
        # We use a very small TTL and sleep a bit more than it
        await async_inmemory.set("exp2", "val2", ttl=1)
        await asyncio.sleep(1.05)
        assert await async_inmemory.get("exp2") is None

    async def test_delete_all(self, async_inmemory: AsyncInMemoryCache) -> None:
        """delete_all clears everything."""
        await async_inmemory.set("a", 1)
        await async_inmemory.set("b", 2)
        await async_inmemory.delete_all()
        assert await async_inmemory.get("a") is None
        assert await async_inmemory.get("b") is None

    async def test_delete_by_pattern(self, async_inmemory: AsyncInMemoryCache) -> None:
        """delete_by_pattern removes matching keys."""
        await async_inmemory.set("prefix:a", 1)
        await async_inmemory.set("prefix:b", 2)
        await async_inmemory.set("other:c", 3)
        await async_inmemory.delete_by_pattern("prefix:*")
        assert await async_inmemory.get("prefix:a") is None
        assert await async_inmemory.get("prefix:b") is None
        assert await async_inmemory.get("other:c") == 3

    async def test_delete_by_pattern_with_params(self, async_inmemory: AsyncInMemoryCache) -> None:
        """delete_by_pattern with params only deletes matching keys containing param."""
        await async_inmemory.set("fn|(user_id=1)::mod.fn", 1)
        await async_inmemory.set("fn|(user_id=2)::mod.fn", 2)
        await async_inmemory.delete_by_pattern("fn|(*)::mod.fn", ["user_id=1"])
        assert await async_inmemory.get("fn|(user_id=1)::mod.fn") is None
        assert await async_inmemory.get("fn|(user_id=2)::mod.fn") == 2


class TestSyncInMemoryCache:
    """Tests for SyncInMemoryCache."""

    def test_set_and_get(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Set a value and retrieve it."""
        sync_inmemory.set("key", "value")
        assert sync_inmemory.get("key") == "value"

    def test_get_missing(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Get returns None for missing key."""
        assert sync_inmemory.get("missing") is None

    def test_delete(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Delete removes a key."""
        sync_inmemory.set("k", "v")
        sync_inmemory.delete("k")
        assert sync_inmemory.get("k") is None

    def test_delete_missing(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Delete on missing key does not raise."""
        sync_inmemory.delete("ghost")

    def test_exists_true(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Exists returns True for existing key."""
        sync_inmemory.set("k", "v")
        assert sync_inmemory.exists("k") is True

    def test_exists_false(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Exists returns False for missing key."""
        assert sync_inmemory.exists("absent") is False

    def test_ttl_expiry(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Value expires after TTL."""
        sync_inmemory.set("exp", "val", ttl=1)
        assert sync_inmemory.get("exp") == "val"
        time.sleep(1.05)
        assert sync_inmemory.get("exp") is None

    def test_delete_all(self, sync_inmemory: SyncInMemoryCache) -> None:
        """delete_all clears everything."""
        sync_inmemory.set("a", 1)
        sync_inmemory.set("b", 2)
        sync_inmemory.delete_all()
        assert sync_inmemory.get("a") is None

    def test_delete_by_pattern(self, sync_inmemory: SyncInMemoryCache) -> None:
        """delete_by_pattern removes matching keys."""
        sync_inmemory.set("ns:a", 1)
        sync_inmemory.set("ns:b", 2)
        sync_inmemory.set("other", 3)
        sync_inmemory.delete_by_pattern("ns:*")
        assert sync_inmemory.get("ns:a") is None
        assert sync_inmemory.get("ns:b") is None
        assert sync_inmemory.get("other") == 3

    def test_delete_by_pattern_with_params(self, sync_inmemory: SyncInMemoryCache) -> None:
        """delete_by_pattern with params filters correctly."""
        sync_inmemory.set("fn|(id=1)::m.fn", "a")
        sync_inmemory.set("fn|(id=2)::m.fn", "b")
        sync_inmemory.delete_by_pattern("fn|(*)::m.fn", ["id=1"])
        assert sync_inmemory.get("fn|(id=1)::m.fn") is None
        assert sync_inmemory.get("fn|(id=2)::m.fn") == "b"
