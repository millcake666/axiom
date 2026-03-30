"""Tests for SyncRedisClient."""

from __future__ import annotations

import pytest

from axiom.redis.sync_client import SyncRedisClient
from axiom.redis.exception import RedisOperationError


class TestSyncRedisClientGetSet:
    """Tests for get/set operations."""

    def test_set_and_get(self, sync_client: SyncRedisClient) -> None:
        """Set a value and retrieve it."""
        sync_client.set("key1", b"value1")
        result = sync_client.get("key1")
        assert result == b"value1"

    def test_get_missing_key(self, sync_client: SyncRedisClient) -> None:
        """Get returns None for a missing key."""
        result = sync_client.get("nonexistent")
        assert result is None

    def test_set_with_ttl(self, sync_client: SyncRedisClient) -> None:
        """Set a value with TTL and verify it was stored."""
        sync_client.set("ttl_key", b"data", ttl=60)
        result = sync_client.get("ttl_key")
        assert result == b"data"

    def test_set_overwrites(self, sync_client: SyncRedisClient) -> None:
        """Setting the same key twice overwrites."""
        sync_client.set("key", b"first")
        sync_client.set("key", b"second")
        result = sync_client.get("key")
        assert result == b"second"


class TestSyncRedisClientDelete:
    """Tests for delete operations."""

    def test_delete_existing_key(self, sync_client: SyncRedisClient) -> None:
        """Deleting an existing key removes it."""
        sync_client.set("del_key", b"val")
        sync_client.delete("del_key")
        result = sync_client.get("del_key")
        assert result is None

    def test_delete_missing_key(self, sync_client: SyncRedisClient) -> None:
        """Deleting a non-existent key does not raise."""
        sync_client.delete("ghost_key")

    def test_delete_multiple_keys(self, sync_client: SyncRedisClient) -> None:
        """Deleting multiple keys at once."""
        sync_client.set("k1", b"v1")
        sync_client.set("k2", b"v2")
        sync_client.delete("k1", "k2")
        assert sync_client.get("k1") is None
        assert sync_client.get("k2") is None


class TestSyncRedisClientExists:
    """Tests for exists operations."""

    def test_exists_true(self, sync_client: SyncRedisClient) -> None:
        """Exists returns True for an existing key."""
        sync_client.set("exists_key", b"v")
        assert sync_client.exists("exists_key") is True

    def test_exists_false(self, sync_client: SyncRedisClient) -> None:
        """Exists returns False for a missing key."""
        assert sync_client.exists("no_such_key") is False


class TestSyncRedisClientTTL:
    """Tests for TTL-related operations."""

    def test_ttl_with_expiry(self, sync_client: SyncRedisClient) -> None:
        """TTL returns a positive value for a key with expiry."""
        sync_client.set("exp_key", b"v", ttl=30)
        result = sync_client.ttl("exp_key")
        assert result > 0

    def test_ttl_without_expiry(self, sync_client: SyncRedisClient) -> None:
        """TTL returns -1 for a key without expiry."""
        sync_client.set("no_exp_key", b"v")
        result = sync_client.ttl("no_exp_key")
        assert result == -1

    def test_ttl_missing_key(self, sync_client: SyncRedisClient) -> None:
        """TTL returns -2 for a non-existent key."""
        result = sync_client.ttl("ghost")
        assert result == -2

    def test_expire(self, sync_client: SyncRedisClient) -> None:
        """expire() sets TTL on a key."""
        sync_client.set("e_key", b"v")
        sync_client.expire("e_key", 100)
        result = sync_client.ttl("e_key")
        assert result > 0


class TestSyncRedisClientScanIter:
    """Tests for scan_iter."""

    def test_scan_iter_matches(self, sync_client: SyncRedisClient) -> None:
        """scan_iter yields matching keys."""
        sync_client.set("prefix:a", b"1")
        sync_client.set("prefix:b", b"2")
        sync_client.set("other:c", b"3")
        keys = list(sync_client.scan_iter("prefix:*"))
        assert set(keys) == {"prefix:a", "prefix:b"}

    def test_scan_iter_no_match(self, sync_client: SyncRedisClient) -> None:
        """scan_iter returns nothing when no keys match."""
        keys = list(sync_client.scan_iter("zzz:*"))
        assert keys == []


class TestSyncRedisClientFlushall:
    """Tests for flushall."""

    def test_flushall_clears_all(self, sync_client: SyncRedisClient) -> None:
        """flushall removes all keys."""
        sync_client.set("k1", b"v")
        sync_client.set("k2", b"v")
        sync_client.flushall()
        assert sync_client.get("k1") is None
        assert sync_client.get("k2") is None


class TestSyncRedisClientRaw:
    """Tests for raw property."""

    def test_raw_returns_client(self, sync_client: SyncRedisClient) -> None:
        """raw property returns the underlying client."""
        assert sync_client.raw is not None
