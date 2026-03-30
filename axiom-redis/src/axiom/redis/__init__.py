"""axiom.redis — Redis client and utilities."""

__version__ = "0.1.0"

from axiom.redis.async_client import AsyncRedisClient, create_async_redis_client
from axiom.redis.exception import (
    AxiomRedisError,
    RedisConfigurationError,
    RedisConnectionError,
    RedisOperationError,
)
from axiom.redis.settings import RedisSettings
from axiom.redis.sync_client import SyncRedisClient, create_sync_redis_client

__all__ = [
    "AsyncRedisClient",
    "AxiomRedisError",
    "RedisConfigurationError",
    "RedisConnectionError",
    "RedisOperationError",
    "RedisSettings",
    "SyncRedisClient",
    "create_async_redis_client",
    "create_sync_redis_client",
]
