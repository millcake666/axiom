"""Tests for AsyncRedisClient."""

from __future__ import annotations

import pytest

from axiom.redis.async_client import AsyncRedisClient
from axiom.redis.exception import RedisOperationError


class TestAsyncRedisClientGetSet:
    """Tests for get/set operations."""

    async def test_set_and_get(self, async_client: AsyncRedisClient) -> None:
        """Set a value and retrieve it."""
        await async_client.set("key1", b"value1")
        result = await async_client.get("key1")
        assert result == b"value1"

    async def test_get_missing_key(self, async_client: AsyncRedisClient) -> None:
        """Get returns None for a missing key."""
        result = await async_client.get("nonexistent")
        assert result is None

    async def test_set_with_ttl(self, async_client: AsyncRedisClient) -> None:
        """Set a value with TTL and verify it was stored."""
        await async_client.set("ttl_key", b"data", ttl=60)
        result = await async_client.get("ttl_key")
        assert result == b"data"

    async def test_set_overwrites(self, async_client: AsyncRedisClient) -> None:
        """Setting the same key twice overwrites."""
        await async_client.set("key", b"first")
        await async_client.set("key", b"second")
        result = await async_client.get("key")
        assert result == b"second"


class TestAsyncRedisClientDelete:
    """Tests for delete operations."""

    async def test_delete_existing_key(self, async_client: AsyncRedisClient) -> None:
        """Deleting an existing key removes it."""
        await async_client.set("del_key", b"val")
        await async_client.delete("del_key")
        result = await async_client.get("del_key")
        assert result is None

    async def test_delete_missing_key(self, async_client: AsyncRedisClient) -> None:
        """Deleting a non-existent key does not raise."""
        await async_client.delete("ghost_key")

    async def test_delete_multiple_keys(self, async_client: AsyncRedisClient) -> None:
        """Deleting multiple keys at once."""
        await async_client.set("k1", b"v1")
        await async_client.set("k2", b"v2")
        await async_client.delete("k1", "k2")
        assert await async_client.get("k1") is None
        assert await async_client.get("k2") is None


class TestAsyncRedisClientExists:
    """Tests for exists operations."""

    async def test_exists_true(self, async_client: AsyncRedisClient) -> None:
        """Exists returns True for an existing key."""
        await async_client.set("exists_key", b"v")
        assert await async_client.exists("exists_key") is True

    async def test_exists_false(self, async_client: AsyncRedisClient) -> None:
        """Exists returns False for a missing key."""
        assert await async_client.exists("no_such_key") is False


class TestAsyncRedisClientTTL:
    """Tests for TTL-related operations."""

    async def test_ttl_with_expiry(self, async_client: AsyncRedisClient) -> None:
        """TTL returns a positive value for a key with expiry."""
        await async_client.set("exp_key", b"v", ttl=30)
        result = await async_client.ttl("exp_key")
        assert result > 0

    async def test_ttl_without_expiry(self, async_client: AsyncRedisClient) -> None:
        """TTL returns -1 for a key without expiry."""
        await async_client.set("no_exp_key", b"v")
        result = await async_client.ttl("no_exp_key")
        assert result == -1

    async def test_ttl_missing_key(self, async_client: AsyncRedisClient) -> None:
        """TTL returns -2 for a non-existent key."""
        result = await async_client.ttl("ghost")
        assert result == -2

    async def test_expire(self, async_client: AsyncRedisClient) -> None:
        """expire() sets TTL on a key."""
        await async_client.set("e_key", b"v")
        await async_client.expire("e_key", 100)
        result = await async_client.ttl("e_key")
        assert result > 0


class TestAsyncRedisClientScanIter:
    """Tests for scan_iter."""

    async def test_scan_iter_matches(self, async_client: AsyncRedisClient) -> None:
        """scan_iter yields matching keys."""
        await async_client.set("prefix:a", b"1")
        await async_client.set("prefix:b", b"2")
        await async_client.set("other:c", b"3")
        keys = [k async for k in async_client.scan_iter("prefix:*")]
        assert set(keys) == {"prefix:a", "prefix:b"}

    async def test_scan_iter_no_match(self, async_client: AsyncRedisClient) -> None:
        """scan_iter returns nothing when no keys match."""
        keys = [k async for k in async_client.scan_iter("zzz:*")]
        assert keys == []


class TestAsyncRedisClientFlushall:
    """Tests for flushall."""

    async def test_flushall_clears_all(self, async_client: AsyncRedisClient) -> None:
        """flushall removes all keys."""
        await async_client.set("k1", b"v")
        await async_client.set("k2", b"v")
        await async_client.flushall()
        assert await async_client.get("k1") is None
        assert await async_client.get("k2") is None


class TestAsyncRedisClientRaw:
    """Tests for raw property."""

    async def test_raw_returns_client(self, async_client: AsyncRedisClient) -> None:
        """raw property returns the underlying client."""
        assert async_client.raw is not None
