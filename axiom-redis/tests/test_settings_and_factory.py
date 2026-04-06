"""Tests for RedisSettings and factory functions."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from axiom.redis.async_client import AsyncRedisClient, create_async_redis_client
from axiom.redis.exception import RedisOperationError
from axiom.redis.settings import RedisSettings
from axiom.redis.sync_client import SyncRedisClient, create_sync_redis_client


class TestRedisSettings:
    """Tests for RedisSettings defaults."""

    def test_defaults(self) -> None:
        """Default settings are sensible."""
        s = RedisSettings()
        assert s.REDIS_URL == "redis://localhost:6379"
        assert s.REDIS_USE_CLUSTER is False
        assert s.REDIS_MAX_CONNECTIONS is None
        assert s.REDIS_SOCKET_TIMEOUT is None
        assert s.REDIS_DECODE_RESPONSES is False

    def test_custom_url(self) -> None:
        """Custom URL is respected."""
        s = RedisSettings(REDIS_URL="redis://myhost:6380")
        assert s.REDIS_URL == "redis://myhost:6380"


class TestCreateAsyncRedisClient:
    """Tests for create_async_redis_client factory."""

    def test_creates_client(self) -> None:
        """Factory returns an AsyncRedisClient."""
        settings = RedisSettings()
        client = create_async_redis_client(settings)
        assert isinstance(client, AsyncRedisClient)

    def test_with_max_connections(self) -> None:
        """Factory accepts REDIS_MAX_CONNECTIONS."""
        settings = RedisSettings(REDIS_MAX_CONNECTIONS=10)
        client = create_async_redis_client(settings)
        assert isinstance(client, AsyncRedisClient)

    def test_with_socket_timeout(self) -> None:
        """Factory accepts REDIS_SOCKET_TIMEOUT."""
        settings = RedisSettings(REDIS_SOCKET_TIMEOUT=5.0)
        client = create_async_redis_client(settings)
        assert isinstance(client, AsyncRedisClient)


class TestCreateSyncRedisClient:
    """Tests for create_sync_redis_client factory."""

    def test_creates_client(self) -> None:
        """Factory returns a SyncRedisClient."""
        settings = RedisSettings()
        client = create_sync_redis_client(settings)
        assert isinstance(client, SyncRedisClient)

    def test_with_max_connections(self) -> None:
        """Factory accepts REDIS_MAX_CONNECTIONS."""
        settings = RedisSettings(REDIS_MAX_CONNECTIONS=5)
        client = create_sync_redis_client(settings)
        assert isinstance(client, SyncRedisClient)

    def test_with_socket_timeout(self) -> None:
        """Factory accepts REDIS_SOCKET_TIMEOUT."""
        settings = RedisSettings(REDIS_SOCKET_TIMEOUT=2.0)
        client = create_sync_redis_client(settings)
        assert isinstance(client, SyncRedisClient)


class TestAsyncRedisClientErrorPaths:
    """Tests for error handling in AsyncRedisClient."""

    async def test_get_raises_operation_error(self) -> None:
        """GET failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.get.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="GET failed"):
            await client.get("k")

    async def test_set_raises_operation_error(self) -> None:
        """SET failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.set.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="SET failed"):
            await client.set("k", "v")

    async def test_set_with_ttl_raises_operation_error(self) -> None:
        """SET with TTL failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.set.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="SET failed"):
            await client.set("k", "v", ttl=10)

    async def test_delete_raises_operation_error(self) -> None:
        """DELETE failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.delete.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="DELETE failed"):
            await client.delete("k")

    async def test_exists_raises_operation_error(self) -> None:
        """EXISTS failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.exists.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="EXISTS failed"):
            await client.exists("k")

    async def test_expire_raises_operation_error(self) -> None:
        """EXPIRE failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.expire.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="EXPIRE failed"):
            await client.expire("k", 10)

    async def test_ttl_raises_operation_error(self) -> None:
        """TTL failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.ttl.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="TTL failed"):
            await client.ttl("k")

    async def test_flushall_raises_operation_error(self) -> None:
        """FLUSHALL failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.flushall.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="FLUSHALL failed"):
            await client.flushall()

    async def test_close_raises_operation_error(self) -> None:
        """CLOSE failure raises RedisOperationError."""
        mock = AsyncMock()
        mock.aclose.side_effect = RuntimeError("boom")
        client = AsyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="CLOSE failed"):
            await client.close()


class TestSyncRedisClientErrorPaths:
    """Tests for error handling in SyncRedisClient."""

    def test_get_raises_operation_error(self) -> None:
        """GET failure raises RedisOperationError."""
        mock = MagicMock()
        mock.get.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="GET failed"):
            client.get("k")

    def test_set_raises_operation_error(self) -> None:
        """SET failure raises RedisOperationError."""
        mock = MagicMock()
        mock.set.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="SET failed"):
            client.set("k", "v")

    def test_set_with_ttl_raises_operation_error(self) -> None:
        """SET with TTL failure raises RedisOperationError."""
        mock = MagicMock()
        mock.set.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="SET failed"):
            client.set("k", "v", ttl=10)

    def test_delete_raises_operation_error(self) -> None:
        """DELETE failure raises RedisOperationError."""
        mock = MagicMock()
        mock.delete.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="DELETE failed"):
            client.delete("k")

    def test_exists_raises_operation_error(self) -> None:
        """EXISTS failure raises RedisOperationError."""
        mock = MagicMock()
        mock.exists.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="EXISTS failed"):
            client.exists("k")

    def test_expire_raises_operation_error(self) -> None:
        """EXPIRE failure raises RedisOperationError."""
        mock = MagicMock()
        mock.expire.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="EXPIRE failed"):
            client.expire("k", 10)

    def test_ttl_raises_operation_error(self) -> None:
        """TTL failure raises RedisOperationError."""
        mock = MagicMock()
        mock.ttl.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="TTL failed"):
            client.ttl("k")

    def test_flushall_raises_operation_error(self) -> None:
        """FLUSHALL failure raises RedisOperationError."""
        mock = MagicMock()
        mock.flushall.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="FLUSHALL failed"):
            client.flushall()

    def test_close_raises_operation_error(self) -> None:
        """CLOSE failure raises RedisOperationError."""
        mock = MagicMock()
        mock.close.side_effect = RuntimeError("boom")
        client = SyncRedisClient(mock)
        with pytest.raises(RedisOperationError, match="CLOSE failed"):
            client.close()
